from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import BackgroundTasks, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import (
    get_issue,
    get_review,
    get_snapshot,
    init_db,
    list_issues_for_review,
    update_issue_status,
)
from app.models import (
    DismissRequest,
    Issue,
    IssueStatus,
    PackSummary,
    ReviewCreatedResponse,
    ReviewDetailResponse,
    ReviewRequest,
)
from app.reviewer.pack_loader import list_packs
from app.reviews import execute_review, schedule_review
from app.snapshots import create_snapshot


logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="CoReview API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/packs", response_model=list[PackSummary])
async def get_packs() -> list[PackSummary]:
    return list_packs()


@app.post("/reviews", response_model=ReviewCreatedResponse, status_code=202)
async def create_review(
    req: ReviewRequest, background_tasks: BackgroundTasks
) -> ReviewCreatedResponse:
    if not req.html or not req.html.strip():
        raise HTTPException(status_code=400, detail="html is required")
    if not req.pack_id or not req.pack_id.strip():
        raise HTTPException(status_code=400, detail="pack_id is required")

    snapshot = await create_snapshot(req.html)

    try:
        review = await schedule_review(snapshot, req.pack_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    background_tasks.add_task(
        execute_review, review.id, snapshot.html, req.pack_id
    )
    return ReviewCreatedResponse(
        review_id=review.id,
        snapshot_id=snapshot.id,
        status=review.status,
    )


@app.get("/reviews/{review_id}", response_model=ReviewDetailResponse)
async def get_review_detail(review_id: str) -> ReviewDetailResponse:
    review = await get_review(review_id)
    if not review:
        raise HTTPException(status_code=404, detail="review not found")
    issues = await list_issues_for_review(review_id)
    return ReviewDetailResponse(
        review_id=review.id,
        snapshot_id=review.snapshot_id,
        pack_id=review.pack_id,
        status=review.status,
        issues=issues,
        error=review.error,
    )


@app.get("/snapshots/{snapshot_id}/html")
async def get_snapshot_html(snapshot_id: str) -> Response:
    snap = await get_snapshot(snapshot_id)
    if not snap:
        raise HTTPException(status_code=404, detail="snapshot not found")
    return Response(content=snap.html, media_type="text/html; charset=utf-8")


@app.post(
    "/reviews/{review_id}/issues/{issue_id}/accept",
    response_model=Issue,
)
async def accept_issue(review_id: str, issue_id: str) -> Issue:
    issue = await _load_issue_for_review(review_id, issue_id)
    await update_issue_status(
        issue_id,
        IssueStatus.accepted,
        resolved_at=datetime.now(timezone.utc),
        dismissal_reason=None,
    )
    updated = await get_issue(issue_id)
    assert updated is not None
    return updated


@app.post(
    "/reviews/{review_id}/issues/{issue_id}/dismiss",
    response_model=Issue,
)
async def dismiss_issue(
    review_id: str, issue_id: str, req: DismissRequest
) -> Issue:
    reason = (req.reason or "").strip()
    if not reason:
        raise HTTPException(status_code=400, detail="dismissal reason is required")
    issue = await _load_issue_for_review(review_id, issue_id)
    await update_issue_status(
        issue_id,
        IssueStatus.dismissed,
        resolved_at=datetime.now(timezone.utc),
        dismissal_reason=reason,
    )
    updated = await get_issue(issue_id)
    assert updated is not None
    return updated


async def _load_issue_for_review(review_id: str, issue_id: str) -> Issue:
    issue = await get_issue(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="issue not found")
    if issue.review_id != review_id:
        raise HTTPException(status_code=404, detail="issue not found on this review")
    return issue
