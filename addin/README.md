# CoReview Drafting Assistant — Word Add-in

Word taskpane add-in in TypeScript + React 18 + Fluent UI v9. Scaffolded from
`Office-Addin-TaskPane-React` (the OfficeDev template that `yo office` pulls)
and stripped to a single-host (Word) XML-manifest layout.

## Quick start

```bash
cd addin
npm install
npx office-addin-manifest validate manifest.xml
# Confirm the backend is running on http://localhost:8000 first:
#   (cd ../backend && docker compose up)
npm run start
```

`npm run start` uses `office-addin-debugging` to:

1. Generate a trusted localhost HTTPS cert (via `office-addin-dev-certs`).
2. Start the webpack dev server on `https://localhost:3000`.
3. Sideload the manifest into Word.

To stop: `npm run stop`.

## Pointing at a non-default backend

Edit `src/taskpane/taskpane.html` to set `window.__CO_REVIEW_API__` before the
bundle loads, or change `API_BASE` in `src/taskpane/services/api.ts`.

## Layout

```
manifest.xml                  Word taskpane manifest (XML).
webpack.config.js             Dev server + bundling (from OfficeDev template).
src/
├── taskpane/
│   ├── taskpane.html         HTML host.
│   ├── index.tsx             React bootstrap; wraps App in FluentProvider.
│   ├── types.ts              TS mirrors of backend Pydantic models.
│   ├── components/
│   │   ├── Header.tsx
│   │   ├── ReviewControls.tsx   Pack dropdown + Review button.
│   │   ├── IssueCard.tsx        Single issue with Accept/Dismiss.
│   │   ├── IssueList.tsx        Sorted list (severity desc, paragraph asc).
│   │   ├── SnapshotViewer.tsx   Renders /snapshots/{id}/html, highlights.
│   │   └── App.tsx              Top-level layout + state.
│   └── services/
│       ├── api.ts               fetch wrappers around the backend.
│       ├── word.ts              Office.js body.getHtml() helper.
│       └── polling.ts           usePollReview hook.
└── commands/                 Unused FunctionFile target (manifest reference).
```

## What it does

1. Lists available packs via `GET /packs` on mount.
2. On **Review document**: captures `body.getHtml()` from the live Word doc
   and `POST`s it to `/reviews` along with the selected pack id.
3. Polls `GET /reviews/{id}` every 2s until `complete` or `failed`.
4. Renders issues as Fluent UI cards — severity badge, quoted anchor text,
   explanation, guidance, citation chips, Accept / Dismiss buttons.
5. Clicking a card scrolls the snapshot viewer to the matching
   `[data-rid]` paragraph and highlights it.
6. Accept / Dismiss persist to the backend and update the card inline.

## What it does NOT do (deliberately)

- It does not rewrite, replace, or auto-apply changes to the document.
- It does not use native Word comments; the UX is panel cards with
  interactive highlighting on a snapshot.
- It does not re-review on edit. Reviews are discrete events.
- It does not authenticate the add-in → backend hop (tracer bullet only).
