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

from src.models.findings import ReviewFinding, ReviewSummary, Severity
from src.prompts.review_prompt import format_review_prompt

logger = logging.getLogger(__name__)

try:
    from langfuse.decorators import observe
except ImportError:

    def observe(*args, **kwargs):
        """No-op fallback when langfuse is not installed."""
        if args and callable(args[0]):
            return args[0]

        def decorator(fn):
            return fn

        return decorator


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
    file_diffs: list[dict[str, str]]
    filtered_files: list[dict[str, str]]
    findings: list[dict[str, Any]]
    summary: dict[str, Any]
    formatted_review: str
    errors: list[str]


def parse_diff(state: ReviewState) -> ReviewState:
    """Split a unified diff into per-file chunks."""
    raw_diff = state["raw_diff"]
    file_diffs: list[dict[str, str]] = []

    splits = _DIFF_HEADER_RE.split(raw_diff)
    # splits: [preamble, a_path1, b_path1, chunk1, a_path2, b_path2, chunk2, ...]
    i = 1
    while i + 2 < len(splits):
        b_path = splits[i + 1]
        chunk = splits[i + 2]
        file_diffs.append({"path": b_path, "diff": chunk.strip()})
        i += 3

    logger.info("Parsed %d file diffs", len(file_diffs))
    return {"file_diffs": file_diffs}


def filter_files(state: ReviewState) -> ReviewState:
    """Remove non-code files from the diff set."""
    file_diffs = state["file_diffs"]
    filtered: list[dict[str, str]] = []

    for file_diff in file_diffs:
        ext = PurePosixPath(file_diff["path"]).suffix.lower()
        if ext in SKIP_EXTENSIONS:
            logger.debug("Skipping non-code file: %s", file_diff["path"])
            continue
        filtered.append(file_diff)

    logger.info(
        "Filtered to %d code files (skipped %d)",
        len(filtered),
        len(file_diffs) - len(filtered),
    )
    return {"filtered_files": filtered}


def _extract_json_array(text: str) -> list[dict[str, Any]]:
    """Extract a JSON array from LLM output with fallback strategies."""
    stripped = text.strip()

    # Strategy 1: direct parse
    if stripped.startswith("["):
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            pass

    # Strategy 2: extract from markdown code fences
    fence_match = re.search(r"```(?:json)?\s*\n?(.*?)```", stripped, re.DOTALL)
    if fence_match:
        try:
            return json.loads(fence_match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Strategy 3: find any JSON array in the text
    array_match = re.search(r"\[.*]", stripped, re.DOTALL)
    if array_match:
        try:
            return json.loads(array_match.group(0))
        except json.JSONDecodeError:
            pass

    raise json.JSONDecodeError("No JSON array found in response", text, 0)


@observe(name="analyze_single_file")
def _analyze_single_file(
    llm: ChatGroq, path: str, diff: str,
) -> tuple[list[dict[str, Any]], int]:
    """Analyze a single file diff with the LLM."""
    prompt = format_review_prompt(file_diff=diff, file_path=path)
    response = llm.invoke(prompt)
    raw_text = response.content

    token_count = 0
    usage = getattr(response, "usage_metadata", None)
    if usage:
        token_count = usage.get("total_tokens", 0)

    raw_findings = _extract_json_array(raw_text)

    validated: list[dict[str, Any]] = []
    for item in raw_findings:
        try:
            finding = ReviewFinding.model_validate(item)
            validated.append(finding.model_dump())
        except ValidationError as ve:
            logger.warning("Invalid finding for %s: %s", path, ve)

    return validated, token_count


@observe(name="analyze_files")
def analyze_files(state: ReviewState) -> ReviewState:
    """Send each file diff to Groq for analysis sequentially."""
    filtered_files = state["filtered_files"]
    findings: list[dict[str, Any]] = []
    errors: list[str] = []
    total_tokens = 0

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
        api_key=os.environ.get("GROQ_API_KEY"),
    )

    start_time = time.monotonic()

    for idx, file_diff in enumerate(filtered_files):
        path = file_diff["path"]
        diff = file_diff["diff"]
        logger.info("Analyzing file: %s", path)

        try:
            file_findings, tokens = _analyze_single_file(llm, path, diff)
            findings.extend(file_findings)
            total_tokens += tokens
            logger.info("Found %d issues in %s", len(file_findings), path)
        except json.JSONDecodeError as exc:
            msg = f"Failed to parse LLM JSON for {path}: {exc}"
            logger.warning(msg)
            errors.append(msg)
        except Exception as exc:
            msg = f"Error analyzing {path}: {exc}"
            logger.error(msg)
            errors.append(msg)

        # Rate-limit delay between Groq calls (skip after last file)
        if idx < len(filtered_files) - 1:
            time.sleep(1)

    elapsed = time.monotonic() - start_time
    logger.info("Analysis complete in %.2fs, %d total tokens", elapsed, total_tokens)

    return {
        "findings": findings,
        "summary": {"tokens_used": total_tokens, "latency_seconds": elapsed},
        "errors": errors,
    }


def aggregate(state: ReviewState) -> ReviewState:
    """Combine findings into a ReviewSummary."""
    raw_findings = state["findings"]
    partial = state.get("summary", {})

    all_findings: list[ReviewFinding] = []
    for item in raw_findings:
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
    """Convert ReviewSummary to GitHub-formatted markdown."""
    summary = ReviewSummary.model_validate(state["summary"])
    lines: list[str] = []

    critical = summary.stats.get("critical", 0)
    warnings = summary.stats.get("warning", 0)
    suggestions = summary.stats.get("suggestion", 0)

    lines.append("## Code Review Summary")
    lines.append("")
    lines.append(
        f"**{summary.stats.get('total', 0)} issues found** "
        f"({critical} critical, {warnings} warnings, {suggestions} suggestions)"
    )
    lines.append("")
    lines.append(
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

        lines.append(
            f"### {severity_icons[severity]} {severity.value.title()} ({len(matching)})"
        )
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

    lines.append("---")
    lines.append(
        "*This review was generated by an automated analysis. Findings may include "
        "false positives. Always verify suggestions against your project context "
        "and requirements before applying changes.*"
    )

    formatted = "\n".join(lines)
    logger.info("Formatted review (%d chars)", len(formatted))
    return {"formatted_review": formatted}
