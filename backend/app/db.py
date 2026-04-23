from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import aiosqlite

from app.config import settings
from app.models import (
    Citation,
    Issue,
    IssueStatus,
    Review,
    ReviewStatus,
    Severity,
    Snapshot,
)


SCHEMA = """
CREATE TABLE IF NOT EXISTS snapshots (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    html TEXT NOT NULL,
    paragraph_count INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS reviews (
    id TEXT PRIMARY KEY,
    snapshot_id TEXT NOT NULL,
    pack_id TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    completed_at TEXT,
    error TEXT,
    FOREIGN KEY (snapshot_id) REFERENCES snapshots(id)
);

CREATE TABLE IF NOT EXISTS issues (
    id TEXT PRIMARY KEY,
    review_id TEXT NOT NULL,
    paragraph_id TEXT NOT NULL,
    anchor_text TEXT NOT NULL,
    explanation TEXT NOT NULL,
    guidance TEXT NOT NULL,
    severity TEXT NOT NULL,
    confidence REAL NOT NULL,
    citations_json TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    dismissal_reason TEXT,
    resolved_at TEXT,
    FOREIGN KEY (review_id) REFERENCES reviews(id)
);

CREATE INDEX IF NOT EXISTS idx_issues_review ON issues(review_id);
"""


def _sqlite_path() -> str:
    url = settings.DATABASE_URL
    m = re.match(r"sqlite(?:\+aiosqlite)?:///(.+)$", url)
    if not m:
        raise ValueError(f"Unsupported DATABASE_URL: {url}")
    return m.group(1)


async def init_db() -> None:
    path = Path(_sqlite_path())
    path.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(path) as db:
        await db.executescript(SCHEMA)
        await db.commit()


async def _conn() -> aiosqlite.Connection:
    path = Path(_sqlite_path())
    conn = await aiosqlite.connect(path)
    conn.row_factory = aiosqlite.Row
    return conn


def _iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def _parse_iso(s: str | None) -> datetime | None:
    if not s:
        return None
    return datetime.fromisoformat(s)


# --- Snapshots ---


async def insert_snapshot(snapshot: Snapshot) -> None:
    async with await _conn() as db:
        await db.execute(
            "INSERT INTO snapshots (id, created_at, html, paragraph_count) "
            "VALUES (?, ?, ?, ?)",
            (
                snapshot.id,
                _iso(snapshot.created_at),
                snapshot.html,
                snapshot.paragraph_count,
            ),
        )
        await db.commit()


async def get_snapshot(snapshot_id: str) -> Snapshot | None:
    async with await _conn() as db:
        row = await (
            await db.execute("SELECT * FROM snapshots WHERE id = ?", (snapshot_id,))
        ).fetchone()
    if not row:
        return None
    return Snapshot(
        id=row["id"],
        created_at=_parse_iso(row["created_at"]),
        html=row["html"],
        paragraph_count=row["paragraph_count"],
    )


# --- Reviews ---


async def insert_review(review: Review) -> None:
    async with await _conn() as db:
        await db.execute(
            "INSERT INTO reviews (id, snapshot_id, pack_id, status, created_at, "
            "completed_at, error) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                review.id,
                review.snapshot_id,
                review.pack_id,
                review.status.value,
                _iso(review.created_at),
                _iso(review.completed_at) if review.completed_at else None,
                review.error,
            ),
        )
        await db.commit()


async def update_review_status(
    review_id: str,
    status: ReviewStatus,
    completed_at: datetime | None = None,
    error: str | None = None,
) -> None:
    async with await _conn() as db:
        await db.execute(
            "UPDATE reviews SET status = ?, completed_at = ?, error = ? WHERE id = ?",
            (
                status.value,
                _iso(completed_at) if completed_at else None,
                error,
                review_id,
            ),
        )
        await db.commit()


async def get_review(review_id: str) -> Review | None:
    async with await _conn() as db:
        row = await (
            await db.execute("SELECT * FROM reviews WHERE id = ?", (review_id,))
        ).fetchone()
    if not row:
        return None
    return Review(
        id=row["id"],
        snapshot_id=row["snapshot_id"],
        pack_id=row["pack_id"],
        status=ReviewStatus(row["status"]),
        created_at=_parse_iso(row["created_at"]),
        completed_at=_parse_iso(row["completed_at"]),
        error=row["error"],
    )


# --- Issues ---


def _issue_from_row(row: aiosqlite.Row) -> Issue:
    citations_raw = json.loads(row["citations_json"])
    return Issue(
        id=row["id"],
        review_id=row["review_id"],
        paragraph_id=row["paragraph_id"],
        anchor_text=row["anchor_text"],
        explanation=row["explanation"],
        guidance=row["guidance"],
        severity=Severity(row["severity"]),
        confidence=row["confidence"],
        citations=[Citation(**c) for c in citations_raw],
        status=IssueStatus(row["status"]),
        dismissal_reason=row["dismissal_reason"],
        resolved_at=_parse_iso(row["resolved_at"]),
    )


async def insert_issues(issues: list[Issue]) -> None:
    if not issues:
        return
    async with await _conn() as db:
        await db.executemany(
            "INSERT INTO issues (id, review_id, paragraph_id, anchor_text, "
            "explanation, guidance, severity, confidence, citations_json, status, "
            "dismissal_reason, resolved_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    i.id,
                    i.review_id,
                    i.paragraph_id,
                    i.anchor_text,
                    i.explanation,
                    i.guidance,
                    i.severity.value,
                    i.confidence,
                    json.dumps([c.model_dump() for c in i.citations]),
                    i.status.value,
                    i.dismissal_reason,
                    _iso(i.resolved_at) if i.resolved_at else None,
                )
                for i in issues
            ],
        )
        await db.commit()


async def list_issues_for_review(review_id: str) -> list[Issue]:
    async with await _conn() as db:
        rows = await (
            await db.execute(
                "SELECT * FROM issues WHERE review_id = ? ORDER BY severity DESC, "
                "paragraph_id",
                (review_id,),
            )
        ).fetchall()
    return [_issue_from_row(r) for r in rows]


async def get_issue(issue_id: str) -> Issue | None:
    async with await _conn() as db:
        row = await (
            await db.execute("SELECT * FROM issues WHERE id = ?", (issue_id,))
        ).fetchone()
    if not row:
        return None
    return _issue_from_row(row)


async def update_issue_status(
    issue_id: str,
    status: IssueStatus,
    resolved_at: datetime,
    dismissal_reason: str | None = None,
) -> None:
    async with await _conn() as db:
        await db.execute(
            "UPDATE issues SET status = ?, resolved_at = ?, dismissal_reason = ? "
            "WHERE id = ?",
            (status.value, _iso(resolved_at), dismissal_reason, issue_id),
        )
        await db.commit()
