from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class IssueStatus(str, Enum):
    open = "open"
    accepted = "accepted"
    dismissed = "dismissed"


class ReviewStatus(str, Enum):
    pending = "pending"
    running = "running"
    complete = "complete"
    failed = "failed"


class Snapshot(BaseModel):
    id: str
    created_at: datetime
    html: str
    paragraph_count: int


class ReviewRequest(BaseModel):
    html: str
    pack_id: str


class Review(BaseModel):
    id: str
    snapshot_id: str
    pack_id: str
    status: ReviewStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class Citation(BaseModel):
    rule_id: str
    rule_title: str


class Issue(BaseModel):
    id: str
    review_id: str
    paragraph_id: str
    anchor_text: str
    explanation: str
    guidance: str
    severity: Severity
    confidence: float = Field(ge=0.0, le=1.0)
    citations: list[Citation]
    status: IssueStatus = IssueStatus.open
    dismissal_reason: Optional[str] = None
    resolved_at: Optional[datetime] = None


class DismissRequest(BaseModel):
    reason: str


class ReviewCreatedResponse(BaseModel):
    review_id: str
    snapshot_id: str
    status: ReviewStatus


class ReviewDetailResponse(BaseModel):
    review_id: str
    snapshot_id: str
    pack_id: str
    status: ReviewStatus
    issues: list[Issue]
    error: Optional[str] = None


class PackSummary(BaseModel):
    id: str
    name: str
    description: str
    version: str


# --- LLM intermediates (internal, not exposed) ---


class SingleShotIssue(BaseModel):
    paragraph_id: str
    anchor_text: str
    explanation: str
    guidance: str
    severity: Severity
    rule_id: str
    rule_title: str


class SingleShotBatch(BaseModel):
    """Wrapper for the JSON object the reviewer returns per shot."""

    issues: list[SingleShotIssue]


class ConsolidatedIssue(BaseModel):
    paragraph_id: str
    anchor_text: str
    explanation: str
    guidance: str
    severity: Severity
    confidence: float = Field(ge=0.0, le=1.0)
    citations: list[Citation]
    keep: bool
    reason: str


class ConsolidatedBatch(BaseModel):
    issues: list[ConsolidatedIssue]
