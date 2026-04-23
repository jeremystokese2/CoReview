# CoReview — Word Drafting Assistant (Tracer Bullet)

A Word add-in that helps authors draft and develop content by reviewing it
against style guides, policy, compliance, and organisational standards.

This is a **tracer bullet**: the thinnest end-to-end slice that validates the
approach before deeper investment.

## What this proves

1. An Office.js add-in can reliably extract a whole document as HTML.
2. Snapshot-based anchoring (interactive highlighting on a rendered HTML
   snapshot) works cleanly — no bounding boxes required.
3. A rules-in-context reviewer against whole-doc content produces useful,
   non-noisy findings.
4. The three-prompt pattern (guidelines → agent → consolidator) ports
   cleanly off PromptFlow to a plain async Python service.
5. The async job + polling UX feels acceptable in a side panel.

## Layout

```
backend/   FastAPI + Agent Framework + SQLite. Dockerised.
addin/     Word taskpane add-in: TypeScript, React 18, Fluent UI v9.
```

See `backend/README.md` and `addin/README.md` for per-package instructions.

## How a review flows

What happens when an author clicks **Review document** in the side panel.
Top-to-bottom is time; arrows are data or HTTP calls.

```mermaid
sequenceDiagram
    autonumber
    actor Author
    participant Taskpane as Side panel<br/>(React)
    participant Word as Word<br/>(Office.js)
    participant API as FastAPI
    participant BG as Background task
    participant DB as SQLite
    participant Reviewer as Reviewer agent<br/>(×3, temp 1.0)
    participant Consolidator as Consolidator agent<br/>(×1, temp 0.2)
    participant Foundry as Azure AI Foundry<br/>(Claude Sonnet 4.6)

    Author->>Taskpane: Click "Review document"
    Taskpane->>Word: body.getHtml()
    Word-->>Taskpane: raw document HTML
    Taskpane->>API: POST /reviews {html, pack_id}

    rect rgb(245,245,245)
    note right of API: Snapshot ingest (sync)
    API->>API: normalise HTML<br/>(strip scripts/styles,<br/>stamp data-rid on blocks)
    API->>DB: insert snapshot
    API->>DB: insert review (status=pending)
    end

    API-->>Taskpane: 202 {review_id, snapshot_id}
    API->>BG: schedule execute_review

    loop every 2s until terminal
        Taskpane->>API: GET /reviews/{id}
        API->>DB: read review + issues
        API-->>Taskpane: {status, issues[]}
    end

    rect rgb(245,245,245)
    note right of BG: Reviewer pipeline (async)
    BG->>BG: load pack<br/>render reviewer.jinja2
    par shot 1
        BG->>Reviewer: snapshot HTML + instructions
        Reviewer->>Foundry: chat completion
        Foundry-->>Reviewer: JSON
        Reviewer-->>BG: SingleShotIssue[]
    and shot 2
        BG->>Reviewer: snapshot HTML + instructions
        Reviewer->>Foundry: chat completion
        Foundry-->>Reviewer: JSON
        Reviewer-->>BG: SingleShotIssue[]
    and shot 3
        BG->>Reviewer: snapshot HTML + instructions
        Reviewer->>Foundry: chat completion
        Foundry-->>Reviewer: JSON
        Reviewer-->>BG: SingleShotIssue[]
    end
    BG->>BG: aggregate shots<br/>render consolidator.jinja2
    BG->>Consolidator: aggregated JSON
    Consolidator->>Foundry: chat completion
    Foundry-->>Consolidator: JSON
    Consolidator-->>BG: ConsolidatedIssue[]<br/>(keep, confidence, citations)
    BG->>BG: filter by keep flag<br/>and confidence threshold
    BG->>DB: insert issues
    BG->>DB: update review (status=complete)
    end

    Taskpane->>API: GET /reviews/{id} (next poll)
    API-->>Taskpane: {status:complete, issues[]}
    Taskpane->>API: GET /snapshots/{id}/html
    API-->>Taskpane: normalised HTML
    Taskpane-->>Author: render issue cards<br/>+ snapshot viewer

    Author->>Taskpane: Click card
    Taskpane->>Taskpane: scroll + highlight<br/>[data-rid=p_N] in snapshot

    Author->>Taskpane: Accept / Dismiss(reason)
    Taskpane->>API: POST /reviews/{id}/issues/{id}/{accept|dismiss}
    API->>DB: update issue
    API-->>Taskpane: updated Issue
```

Key properties worth calling out:

- **One HTML capture, one canonical version.** The raw HTML from Word is
  normalised once at ingest and stored immutably; every subsequent highlight
  and every agent call targets that same snapshot.
- **Multi-shot diversity, single consolidation.** Three reviewer shots run
  concurrently at temperature 1.0 (`asyncio.gather`). A single consolidator
  pass at temperature 0.2 dedupes, scores confidence, and decides keep/drop.
- **No streaming.** Issues become visible to the taskpane only when the
  consolidator returns and the batch lands in SQLite. Status + issues-so-far
  are exposed via polling.
- **Guidance, not rewrites.** Every issue carries `explanation` + `guidance`
  (prose advice). The schema has no `suggested_fix` field. Authors decide.

## Core principles

- **Human in the loop.** The tool never rewrites content. It surfaces issues,
  explanations, and guidance. The author decides.
- **Snapshot-as-substrate.** Every review targets an immutable snapshot of
  the document at review time. Highlights render against the snapshot.
- **Whole-doc context.** The entire document goes into the LLM call in a
  single pass.
- **Review packs are first-class.** A pack is a named, governed unit of
  rules.
- **Rules in context, not RAG.** All rules go directly into the prompt.
- **Async with polling.** `POST /reviews` schedules a background task; the
  client polls `GET /reviews/{id}` every 2s.
