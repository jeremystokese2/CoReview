from __future__ import annotations

import asyncio
import json
import logging
import re
import uuid
from datetime import datetime, timezone

from pydantic import ValidationError

from app.config import settings
from app.models import (
    ConsolidatedBatch,
    ConsolidatedIssue,
    Issue,
    IssueStatus,
    SingleShotBatch,
    SingleShotIssue,
)
from app.reviewer.agents import (
    AgentHandle,
    build_consolidator_agent,
    build_reviewer_agent,
)
from app.reviewer.pack_loader import Pack
from app.reviewer.prompts import (
    render_consolidator_instructions,
    render_reviewer_instructions,
)


log = logging.getLogger(__name__)


MAX_JSON_REPAIR_ATTEMPTS = 2


def _strip_fences(text: str) -> str:
    """Remove ```json ... ``` fences if the model wraps the JSON."""
    t = text.strip()
    if t.startswith("```"):
        # Strip opening fence and language hint.
        t = re.sub(r"^```(?:json)?\s*\n?", "", t)
        # Strip closing fence.
        t = re.sub(r"\n?```\s*$", "", t)
    return t.strip()


async def _run_with_json_retry(
    agent: AgentHandle,
    user_message: str,
    model_cls: type,
) -> object | None:
    """Run the agent and parse its response as `model_cls`.

    On ValidationError, feed the error back to the model (up to
    MAX_JSON_REPAIR_ATTEMPTS times). Returns None if parsing never succeeds.
    """
    attempt = 0
    last_err: str | None = None
    prompt = user_message
    while attempt <= MAX_JSON_REPAIR_ATTEMPTS:
        raw = await agent.run(prompt)
        text = _strip_fences(raw)
        try:
            return model_cls.model_validate_json(text)
        except ValidationError as e:
            last_err = str(e)
            log.warning(
                "Agent %s returned invalid JSON (attempt %s): %s",
                agent.name,
                attempt,
                last_err,
            )
            prompt = (
                "Your previous response failed schema validation with this error:\n"
                f"{last_err}\n\n"
                "Return a JSON object that matches the schema exactly. "
                "Do not include any prose outside the JSON object."
            )
            attempt += 1
        except json.JSONDecodeError as e:
            last_err = str(e)
            log.warning(
                "Agent %s returned non-JSON (attempt %s): %s",
                agent.name,
                attempt,
                last_err,
            )
            prompt = (
                "Your previous response was not valid JSON. "
                "Return a JSON object only, matching the requested schema. "
                "No markdown fences, no prose."
            )
            attempt += 1
    log.error("Agent %s failed JSON parsing after %s attempts", agent.name, attempt)
    return None


async def _run_single_shot(agent: AgentHandle, snapshot_html: str) -> list[SingleShotIssue]:
    batch = await _run_with_json_retry(agent, snapshot_html, SingleShotBatch)
    if not isinstance(batch, SingleShotBatch):
        return []
    return batch.issues


def _filter_consolidated(issues: list[ConsolidatedIssue]) -> list[ConsolidatedIssue]:
    out: list[ConsolidatedIssue] = []
    for c in issues:
        if not c.keep:
            continue
        if c.confidence < 0.3 and c.severity.value != "high":
            continue
        out.append(c)
    return out


def _to_issue_row(review_id: str, c: ConsolidatedIssue) -> Issue:
    return Issue(
        id=f"i_{uuid.uuid4().hex[:12]}",
        review_id=review_id,
        paragraph_id=c.paragraph_id,
        anchor_text=c.anchor_text,
        explanation=c.explanation,
        guidance=c.guidance,
        severity=c.severity,
        confidence=c.confidence,
        citations=c.citations,
        status=IssueStatus.open,
    )


async def run_review(review_id: str, snapshot_html: str, pack: Pack) -> list[Issue]:
    """Execute the two-step review: multi-shot reviewer -> consolidator.

    Returns the final filtered list of Issue rows ready for DB insert.
    Raises on unrecoverable errors; callers should wrap and mark the
    review as failed.
    """
    reviewer_instructions = render_reviewer_instructions(pack)
    consolidator_instructions = render_consolidator_instructions(pack)

    reviewer_agent = build_reviewer_agent(pack, reviewer_instructions)
    consolidator_agent = build_consolidator_agent(pack, consolidator_instructions)

    # Step 1: multi-shot reviewer.
    n_shots = max(1, settings.REVIEWER_SHOTS)
    log.info("Review %s: running %d reviewer shots", review_id, n_shots)
    shot_results = await asyncio.gather(
        *[_run_single_shot(reviewer_agent, snapshot_html) for _ in range(n_shots)],
        return_exceptions=True,
    )

    shots: list[list[SingleShotIssue]] = []
    for r in shot_results:
        if isinstance(r, Exception):
            log.warning("Review %s: reviewer shot raised: %s", review_id, r)
            continue
        shots.append(r)

    if not shots:
        raise RuntimeError("All reviewer shots failed")

    log.info(
        "Review %s: %d/%d shots valid, %d total candidate issues",
        review_id,
        len(shots),
        n_shots,
        sum(len(s) for s in shots),
    )

    # Step 2: consolidator.
    aggregated = {
        "shots": [
            [issue.model_dump() for issue in shot]
            for shot in shots
        ]
    }
    consolidated = await _run_with_json_retry(
        consolidator_agent,
        json.dumps(aggregated),
        ConsolidatedBatch,
    )
    if not isinstance(consolidated, ConsolidatedBatch):
        raise RuntimeError("Consolidator returned invalid JSON after retries")

    kept = _filter_consolidated(consolidated.issues)
    log.info(
        "Review %s: consolidator kept %d/%d issues",
        review_id,
        len(kept),
        len(consolidated.issues),
    )

    return [_to_issue_row(review_id, c) for c in kept]


# Re-exported for callers that want a timestamp in UTC.
def now_utc() -> datetime:
    return datetime.now(timezone.utc)
