"""LangGraph node functions for the code review pipeline."""

from __future__ import annotations

import json
import logging
import os
import re
import time
from pathlib import PurePosixPath
from typing import Any, TypedDict

from langchain_groq import ChatGroq
from pydantic import ValidationError

from src.models.findings import Category, ReviewFinding, ReviewSummary, Severity
from src.prompts.review_prompt import format_review_prompt

logger = logging.getLogger(__name__)

SKIP_EXTENSIONS = frozenset({
    ".lock", ".md", ".json", ".yaml", ".yml", ".toml",
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
    ".woff", ".woff2", ".ttf", ".eot",
    ".pyc", ".pyo", ".so", ".dll",
})

_DIFF_HEADER_RE = re.compile(r"^diff --git a/(.+?) b/(.+)$", re.MULTILINE)


class ReviewState(TypedDict, total=False):
    """State passed through the LangGraph review pipeline."""

    pr_url: str
    raw_diff: str
    file_diffs: dict[str, str]
    filtered_diffs: dict[str, str]
    file_findings: dict[str, list[dict[str, Any]]]
    summary: dict[str, Any]
    formatted_review: str


def parse_diff(state: ReviewState) -> ReviewState:
    """Split a unified diff into per-file chunks.

    Args:
        state: Pipeline state containing raw_diff.

    Returns:
        Updated state with file_diffs mapping file paths to their diff chunks.
    """
    raw_diff = state["raw_diff"]
    file_diffs: dict[str, str] = {}

    splits = _DIFF_HEADER_RE.split(raw_diff)
    # splits: [preamble, a_path1, b_path1, chunk1, a_path2, b_path2, chunk2, ...]
    # Skip preamble (index 0), then process in groups of 3
    i = 1
    while i + 2 < len(splits):
        _a_path = splits[i]
        b_path = splits[i + 1]
        chunk = splits[i + 2]
        file_diffs[b_path] = chunk.strip()
        i += 3

    logger.info("Parsed %d file diffs", len(file_diffs))
    return {"file_diffs": file_diffs}


def filter_files(state: ReviewState) -> ReviewState:
    """Remove non-code files from the diff set.

    Args:
        state: Pipeline state containing file_diffs.

    Returns:
        Updated state with filtered_diffs containing only code files.
    """
    file_diffs = state["file_diffs"]
    filtered: dict[str, str] = {}

    for path, diff in file_diffs.items():
        ext = PurePosixPath(path).suffix.lower()
        if ext in SKIP_EXTENSIONS:
            logger.debug("Skipping non-code file: %s", path)
            continue
        filtered[path] = diff

    logger.info(
        "Filtered to %d code files (skipped %d)",
        len(filtered),
        len(file_diffs) - len(filtered),
    )
    return {"filtered_diffs": filtered}


def _extract_json_array(text: str) -> list[dict[str, Any]]:
    """Extract a JSON array from LLM output, handling markdown fences.

    Args:
        text: Raw LLM response text.

    Returns:
        Parsed list of dicts.

    Raises:
        json.JSONDecodeError: If no valid JSON array can be extracted.
    """
    # Try direct parse first
    stripped = text.strip()
    if stripped.startswith("["):
        return json.loads(stripped)

    # Strip markdown code fences
    fence_match = re.search(r"```(?:json)?\s*\n?(.*?)```", stripped, re.DOTALL)
    if fence_match:
        return json.loads(fence_match.group(1).strip())

    raise json.JSONDecodeError("No JSON array found in response", text, 0)


def analyze_file(state: ReviewState) -> ReviewState:
    """Send each file diff to Groq for analysis.

    Args:
        state: Pipeline state containing filtered_diffs.

    Returns:
        Updated state with file_findings, plus token/latency metadata.
    """
    filtered_diffs = state["filtered_diffs"]
    file_findings: dict[str, list[dict[str, Any]]] = {}
    total_tokens = 0

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
        api_key=os.environ.get("GROQ_API_KEY"),
    )

    callbacks = []
    try:
        from langfuse.callback import CallbackHandler as LangfuseCallbackHandler

        langfuse_handler = LangfuseCallbackHandler()
        callbacks.append(langfuse_handler)
    except (ImportError, Exception) as exc:
        logger.warning("Langfuse callback not available: %s", exc)

    start_time = time.monotonic()

    for path, diff in filtered_diffs.items():
        logger.info("Analyzing file: %s", path)
        prompt = format_review_prompt(file_diff=diff, file_path=path)

        try:
            response = llm.invoke(prompt, config={"callbacks": callbacks})
            raw_text = response.content

            token_usage = getattr(response, "usage_metadata", None)
            if token_usage:
                total_tokens += token_usage.get("total_tokens", 0)

            raw_findings = _extract_json_array(raw_text)

            validated: list[dict[str, Any]] = []
            for item in raw_findings:
                try:
                    finding = ReviewFinding.model_validate(item)
                    validated.append(finding.model_dump())
                except ValidationError as ve:
                    logger.warning("Invalid finding for %s: %s", path, ve)

            file_findings[path] = validated
            logger.info("Found %d issues in %s", len(validated), path)

        except json.JSONDecodeError as exc:
            logger.warning("Failed to parse LLM JSON for %s: %s", path, exc)
            file_findings[path] = []
        except Exception as exc:
            logger.error("Error analyzing %s: %s", path, exc)
            file_findings[path] = []

    elapsed = time.monotonic() - start_time
    logger.info("Analysis complete in %.2fs, %d total tokens", elapsed, total_tokens)

    return {
        "file_findings": file_findings,
        "summary": {"tokens_used": total_tokens, "latency_seconds": elapsed},
    }


def aggregate(state: ReviewState) -> ReviewState:
    """Combine per-file findings into a ReviewSummary.

    Args:
        state: Pipeline state containing file_findings and partial summary metadata.

    Returns:
        Updated state with a complete serialized ReviewSummary.
    """
    file_findings = state["file_findings"]
    partial = state.get("summary", {})

    all_findings: list[ReviewFinding] = []
    for findings in file_findings.values():
        for item in findings:
            all_findings.append(ReviewFinding.model_validate(item))

    stats: dict[str, int] = {}
    for finding in all_findings:
        sev = finding.severity.value
        cat = finding.category.value
        stats[sev] = stats.get(sev, 0) + 1
        stats[cat] = stats.get(cat, 0) + 1
    stats["total"] = len(all_findings)

    summary = ReviewSummary(
        findings=all_findings,
        stats=stats,
        model_used="llama-3.3-70b-versatile",
        tokens_used=partial.get("tokens_used", 0),
        latency_seconds=partial.get("latency_seconds", 0.0),
        cost_estimate=0.0,
    )

    logger.info("Aggregated %d findings", len(all_findings))
    return {"summary": summary.model_dump()}


def format_review(state: ReviewState) -> ReviewState:
    """Convert ReviewSummary to GitHub-formatted markdown.

    Args:
        state: Pipeline state containing the serialized summary.

    Returns:
        Updated state with formatted_review markdown string.
    """
    summary = ReviewSummary.model_validate(state["summary"])
    lines: list[str] = []

    lines.append("## AI Code Review Summary")
    lines.append("")
    lines.append(
        f"**{summary.stats.get('total', 0)} issues found** | "
        f"Model: `{summary.model_used}` | "
        f"Tokens: {summary.tokens_used} | "
        f"Time: {summary.latency_seconds:.1f}s"
    )
    lines.append("")

    severity_order = [Severity.CRITICAL, Severity.WARNING, Severity.SUGGESTION]
    severity_icons = {
        Severity.CRITICAL: "🔴",
        Severity.WARNING: "🟡",
        Severity.SUGGESTION: "🔵",
    }

    for severity in severity_order:
        matching = [f for f in summary.findings if f.severity == severity]
        if not matching:
            continue

        lines.append(f"### {severity_icons[severity]} {severity.value.title()} ({len(matching)})")
        lines.append("")

        for finding in matching:
            lines.append(
                f"- **{finding.file_path}:{finding.line_number}** "
                f"[{finding.category.value}] (confidence: {finding.confidence:.0%})"
            )
            lines.append(f"  {finding.message}")
            if finding.suggested_fix:
                lines.append(f"  > **Fix:** {finding.suggested_fix}")
            lines.append("")

    if not summary.findings:
        lines.append("No issues found. The code looks good!")
        lines.append("")

    formatted = "\n".join(lines)
    logger.info("Formatted review (%d chars)", len(formatted))
    return {"formatted_review": formatted}
