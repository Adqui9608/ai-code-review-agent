"""Prompt templates for code review analysis."""

REVIEW_PROMPT_TEMPLATE = """\
You are an expert code reviewer. Analyze the following git diff for bugs, \
security vulnerabilities, performance issues, and code quality problems.

File: {file_path}

```diff
{file_diff}
```

Return your findings as a JSON array. Each element must follow this schema exactly:

```json
[
  {{
    "file_path": "{file_path}",
    "line_number": 42,
    "severity": "warning",
    "category": "bug",
    "message": "Description of the issue found",
    "confidence": 0.85,
    "suggested_fix": "How to fix the issue, or null if unclear"
  }}
]
```

Field constraints:
- file_path: always use "{file_path}"
- line_number: integer, use the + line numbers from the diff
- severity: one of "critical", "warning", "suggestion"
- category: one of "bug", "security", "performance", "style", "logic"
- message: clear, concise description of the issue
- confidence: float between 0.0 and 1.0
- suggested_fix: string with fix suggestion, or null

Rules:
- Only report real issues, not formatting nitpicks handled by linters.
- Set confidence based on how certain you are about the issue.
- If there are no issues, return an empty array: []
- Return ONLY a valid JSON array. No explanations, no markdown wrapping, no other text.
"""


def format_review_prompt(file_diff: str, file_path: str) -> str:
    """Format the review prompt template with the given file diff."""
    return REVIEW_PROMPT_TEMPLATE.format(
        file_diff=file_diff,
        file_path=file_path,
    )
