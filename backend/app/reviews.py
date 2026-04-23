from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from app.db import (
    insert_issues,
    insert_review,
    update_review_status,
)
from app.models import Review, ReviewStatus, Snapshot
from app.reviewer.pack_loader import load_pack
from app.reviewer.pipeline import run_review


log = logging.getLogger(__name__)


async def schedule_review(snapshot: Snapshot, pack_id: str) -> Review:
    """Create the review row in `pending` state and return it.

    The caller (FastAPI) is responsible for kicking off `execute_review`
    as a BackgroundTask.
    """
    # Validate the pack exists up front so we can fail fast with a 400.
    load_pack(pack_id)

    review = Review(
        id=f"r_{uuid.uuid4().hex[:12]}",
        snapshot_id=snapshot.id,
        pack_id=pack_id,
        status=ReviewStatus.pending,
        created_at=datetime.now(timezone.utc),
    )
    await insert_review(review)
    return review


async def execute_review(review_id: str, snapshot_html: str, pack_id: str) -> None:
    """Run the review pipeline end-to-end. Always updates the review row."""
    log.info("Review %s: starting (pack=%s)", review_id, pack_id)
    try:
        await update_review_status(review_id, ReviewStatus.running)
        pack = load_pack(pack_id)
        issues = await run_review(review_id, snapshot_html, pack)
        await insert_issues(issues)
        await update_review_status(
            review_id,
            ReviewStatus.complete,
            completed_at=datetime.now(timezone.utc),
        )
        log.info("Review %s: complete, %d issues", review_id, len(issues))
    except Exception as e:  # noqa: BLE001 — we must always mark the row
        log.exception("Review %s: failed", review_id)
        await update_review_status(
            review_id,
            ReviewStatus.failed,
            completed_at=datetime.now(timezone.utc),
            error=str(e) or e.__class__.__name__,
        )
