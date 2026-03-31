"""Prompt templates for code review analysis."""

REVIEW_PROMPT_TEMPLATE = """\
You are an expert code reviewer. Analyze the following git diff for bugs, \
security vulnerabilities, performance issues, and code quality problems.

The diff is from the file: {file_path}

```diff
{file_diff}
```

Respond with a JSON array of findings. Each finding must match this exact schema:
{{
  "file_path": "{file_path}",
  "line_number": <int>,
  "severity": "critical" | "warning" | "suggestion",
  "category": "bug" | "security" | "performance" | "style" | "logic",
  "message": "<clear description of the issue>",
  "confidence": <float between 0.0 and 1.0>,
  "suggested_fix": "<optional code fix or null>"
}}

Rules:
- Only report real issues, not formatting nitpicks handled by linters.
- Use the + line numbers from the diff for line_number.
- Set confidence based on how certain you are about the issue.
- If there are no issues, return an empty array: []
- Return ONLY the JSON array, no other text.
"""


def format_review_prompt(file_diff: str, file_path: str) -> str:
    """Format the review prompt template with the given file diff.

    Args:
        file_diff: The unified diff content for a single file.
        file_path: Path of the file being reviewed.

    Returns:
        The formatted prompt string ready for LLM invocation.
    """
    return REVIEW_PROMPT_TEMPLATE.format(
        file_diff=file_diff,
        file_path=file_path,
    )
