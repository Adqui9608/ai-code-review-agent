"""Pydantic models for code review findings and summaries."""

from __future__ import annotations

import enum

from pydantic import BaseModel, ConfigDict, Field


class Severity(str, enum.Enum):
    """Severity level for a review finding."""

    CRITICAL = "critical"
    WARNING = "warning"
    SUGGESTION = "suggestion"


class Category(str, enum.Enum):
    """Category of a review finding."""

    BUG = "bug"
    SECURITY = "security"
    PERFORMANCE = "performance"
    STYLE = "style"
    LOGIC = "logic"


class ReviewFinding(BaseModel):
    """A single code review finding for a specific file and line."""

    model_config = ConfigDict(frozen=True)

    file_path: str
    line_number: int
    severity: Severity
    category: Category
    message: str
    confidence: float = Field(ge=0.0, le=1.0)
    suggested_fix: str | None = None


class ReviewSummary(BaseModel):
    """Aggregated summary of all review findings for a PR."""

    findings: list[ReviewFinding] = Field(default_factory=list)
    stats: dict[str, int] = Field(default_factory=dict)
    model_used: str = ""
    tokens_used: int = 0
    latency_seconds: float = 0.0
    cost_estimate: float = 0.0
