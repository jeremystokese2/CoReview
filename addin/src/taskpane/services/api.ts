import type {
  Issue,
  PackSummary,
  ReviewCreated,
  ReviewDetail,
} from "../types";

// The backend URL. For local dev the backend runs on http://localhost:8000.
// Office.js sideloaded pages run on https://localhost:3000, so the backend
// must set CORS for that origin (it does).
//
// To override at runtime (e.g. pointing at a staging backend), set
// `window.__CO_REVIEW_API__` before the taskpane bootstraps.
declare global {
  interface Window {
    __CO_REVIEW_API__?: string;
  }
}

export const API_BASE: string =
  (typeof window !== "undefined" && window.__CO_REVIEW_API__) ||
  "http://localhost:8000";

async function asJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API ${res.status} ${res.statusText}: ${text}`);
  }
  return (await res.json()) as T;
}

export async function listPacks(signal?: AbortSignal): Promise<PackSummary[]> {
  const res = await fetch(`${API_BASE}/packs`, { signal });
  return asJson<PackSummary[]>(res);
}

export async function createReview(
  html: string,
  packId: string,
  signal?: AbortSignal
): Promise<ReviewCreated> {
  const res = await fetch(`${API_BASE}/reviews`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ html, pack_id: packId }),
    signal,
  });
  return asJson<ReviewCreated>(res);
}

export async function getReview(
  reviewId: string,
  signal?: AbortSignal
): Promise<ReviewDetail> {
  const res = await fetch(`${API_BASE}/reviews/${reviewId}`, { signal });
  return asJson<ReviewDetail>(res);
}

export function snapshotHtmlUrl(snapshotId: string): string {
  return `${API_BASE}/snapshots/${snapshotId}/html`;
}

export async function acceptIssue(
  reviewId: string,
  issueId: string,
  signal?: AbortSignal
): Promise<Issue> {
  const res = await fetch(
    `${API_BASE}/reviews/${reviewId}/issues/${issueId}/accept`,
    { method: "POST", signal }
  );
  return asJson<Issue>(res);
}

export async function dismissIssue(
  reviewId: string,
  issueId: string,
  reason: string,
  signal?: AbortSignal
): Promise<Issue> {
  const res = await fetch(
    `${API_BASE}/reviews/${reviewId}/issues/${issueId}/dismiss`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reason }),
      signal,
    }
  );
  return asJson<Issue>(res);
}
