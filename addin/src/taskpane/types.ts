// TypeScript mirrors of the backend Pydantic models.

export type Severity = "low" | "medium" | "high";
export type IssueStatus = "open" | "accepted" | "dismissed";
export type ReviewStatus = "pending" | "running" | "complete" | "failed";

export interface Citation {
  rule_id: string;
  rule_title: string;
}

export interface Issue {
  id: string;
  review_id: string;
  paragraph_id: string;
  anchor_text: string;
  explanation: string;
  guidance: string;
  severity: Severity;
  confidence: number;
  citations: Citation[];
  status: IssueStatus;
  dismissal_reason: string | null;
  resolved_at: string | null;
}

export interface ReviewDetail {
  review_id: string;
  snapshot_id: string;
  pack_id: string;
  status: ReviewStatus;
  issues: Issue[];
  error: string | null;
}

export interface ReviewCreated {
  review_id: string;
  snapshot_id: string;
  status: ReviewStatus;
}

export interface PackSummary {
  id: string;
  name: string;
  description: string;
  version: string;
}
