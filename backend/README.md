# CoReview Backend

FastAPI service orchestrating document reviews via Microsoft Agent Framework
against Claude models on Azure AI Foundry.

## Quick start (Docker)

```bash
cp .env.example .env
# Fill in ANTHROPIC_FOUNDRY_API_KEY and ANTHROPIC_FOUNDRY_RESOURCE.
docker compose up --build
# Service on http://localhost:8000
curl http://localhost:8000/health
```

## Smoke-test Foundry

After bringing the container up, verify Foundry + Agent Framework:

```bash
docker compose exec backend uv run python scripts/smoke_foundry.py
```

Expect a greeting from the reviewer model. If this fails, fix before
proceeding.

## Endpoints

- `POST /reviews` — kick off a review; returns `review_id` + `snapshot_id`.
- `GET  /reviews/{review_id}` — poll for status + issues.
- `GET  /snapshots/{snapshot_id}/html` — raw normalised HTML for viewer.
- `POST /reviews/{review_id}/issues/{issue_id}/accept` — mark accepted.
- `POST /reviews/{review_id}/issues/{issue_id}/dismiss` — dismiss with reason.
- `GET  /packs` — list available packs.

## Project layout

```
app/
├── main.py               FastAPI app + routes
├── models.py             Pydantic models
├── config.py             Settings (pydantic-settings)
├── db.py                 SQLite schema + aiosqlite helpers
├── snapshots.py          HTML normalisation + snapshot storage
├── reviews.py            Review orchestration (background task)
└── reviewer/
    ├── pack_loader.py    Pack loader
    ├── prompts.py        Jinja rendering
    ├── agents.py         Agent Framework agent construction
    ├── pipeline.py       Reviewer + consolidator flow
    └── prompts/          Default reviewer/consolidator templates
app/packs/                Review packs
scripts/                  One-off scripts (smoke_foundry)
tests/                    Unit tests
```
