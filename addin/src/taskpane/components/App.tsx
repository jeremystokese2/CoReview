import * as React from "react";
import { MessageBar, MessageBarBody, makeStyles, tokens } from "@fluentui/react-components";

import Header from "./Header";
import ReviewControls from "./ReviewControls";
import IssueList from "./IssueList";
import SnapshotViewer from "./SnapshotViewer";
import type { Issue, PackSummary, ReviewDetail } from "../types";
import { acceptIssue, createReview, dismissIssue, listPacks } from "../services/api";
import { getDocumentHtml } from "../services/word";
import { usePollReview } from "../services/polling";

const useStyles = makeStyles({
  root: {
    display: "flex",
    flexDirection: "column",
    height: "100vh",
    backgroundColor: tokens.colorNeutralBackground1,
    color: tokens.colorNeutralForeground1,
  },
  statusStrip: {
    padding: "8px 16px",
    borderBottom: `1px solid ${tokens.colorNeutralStroke2}`,
    fontSize: tokens.fontSizeBase200,
    color: tokens.colorNeutralForeground3,
  },
  sectionHead: {
    padding: "8px 16px",
    fontSize: tokens.fontSizeBase200,
    fontWeight: tokens.fontWeightSemibold,
    color: tokens.colorNeutralForeground3,
    textTransform: "uppercase",
    letterSpacing: "0.04em",
    backgroundColor: tokens.colorNeutralBackground2,
    borderTop: `1px solid ${tokens.colorNeutralStroke2}`,
  },
  issueRegion: {
    maxHeight: "40vh",
    display: "flex",
    flexDirection: "column",
  },
  bannerWrap: {
    padding: "8px 16px",
  },
});

function describeStatus(review: ReviewDetail | null, isPolling: boolean): string {
  if (!review) return "Ready — select a pack and click Review.";
  switch (review.status) {
    case "pending":
      return "Queued…";
    case "running":
      return `Reviewing… (${review.issues.length} issue${review.issues.length === 1 ? "" : "s"} so far)`;
    case "complete":
      return `Complete — ${review.issues.length} issue${review.issues.length === 1 ? "" : "s"}`;
    case "failed":
      return `Failed${review.error ? `: ${review.error}` : ""}`;
    default:
      return isPolling ? "Polling…" : "Idle";
  }
}

const App: React.FC = () => {
  const styles = useStyles();
  const [packs, setPacks] = React.useState<PackSummary[]>([]);
  const [loadingPacks, setLoadingPacks] = React.useState(true);
  const [selectedPackId, setSelectedPackId] = React.useState<string | null>(null);
  const [reviewId, setReviewId] = React.useState<string | null>(null);
  const [snapshotId, setSnapshotId] = React.useState<string | null>(null);
  const [startError, setStartError] = React.useState<string | null>(null);
  const [startBusy, setStartBusy] = React.useState(false);
  const [selectedIssue, setSelectedIssue] = React.useState<Issue | null>(null);
  const [localIssues, setLocalIssues] = React.useState<Record<string, Issue>>({});

  const { review, error: pollError, isPolling } = usePollReview(reviewId);

  // Load packs on mount.
  React.useEffect(() => {
    const ctrl = new AbortController();
    listPacks(ctrl.signal)
      .then((ps) => {
        setPacks(ps);
        if (ps.length > 0) setSelectedPackId(ps[0].id);
      })
      .catch((e: any) => {
        if (e?.name !== "AbortError") setStartError(e?.message ?? String(e));
      })
      .finally(() => setLoadingPacks(false));
    return () => ctrl.abort();
  }, []);

  // Merge any locally-updated issues (accept/dismiss) over polled results.
  const issues: Issue[] = React.useMemo(() => {
    const fromPoll = review?.issues ?? [];
    return fromPoll.map((i) => localIssues[i.id] ?? i);
  }, [review, localIssues]);

  const handleReview = async () => {
    if (!selectedPackId) return;
    setStartError(null);
    setStartBusy(true);
    setLocalIssues({});
    setSelectedIssue(null);
    try {
      const html = await getDocumentHtml();
      if (!html || !html.trim()) {
        throw new Error("The document appears to be empty.");
      }
      const created = await createReview(html, selectedPackId);
      setReviewId(created.review_id);
      setSnapshotId(created.snapshot_id);
    } catch (e: any) {
      setStartError(e?.message ?? String(e));
    } finally {
      setStartBusy(false);
    }
  };

  const handleSelectIssue = (issue: Issue) => {
    setSelectedIssue(issue);
  };

  const handleAccept = async (issue: Issue) => {
    const updated = await acceptIssue(issue.review_id, issue.id);
    setLocalIssues((prev) => ({ ...prev, [updated.id]: updated }));
  };

  const handleDismiss = async (issue: Issue, reason: string) => {
    const updated = await dismissIssue(issue.review_id, issue.id, reason);
    setLocalIssues((prev) => ({ ...prev, [updated.id]: updated }));
  };

  const busy = startBusy || isPolling;
  const status = describeStatus(review, isPolling);
  const emptyMessage =
    review?.status === "complete"
      ? "No issues found — clean draft."
      : review
        ? "No issues yet. The reviewer is still working…"
        : "Run a review to see issues here.";

  return (
    <div className={styles.root}>
      <Header />
      <ReviewControls
        packs={packs}
        selectedPackId={selectedPackId}
        onSelectPack={setSelectedPackId}
        onReview={handleReview}
        busy={busy}
        loadingPacks={loadingPacks}
      />
      <div className={styles.statusStrip}>{status}</div>

      {(startError || pollError) && (
        <div className={styles.bannerWrap}>
          <MessageBar intent="error">
            <MessageBarBody>{startError ?? pollError}</MessageBarBody>
          </MessageBar>
        </div>
      )}

      <div className={styles.sectionHead}>Issues</div>
      <div className={styles.issueRegion}>
        <IssueList
          issues={issues}
          selectedIssueId={selectedIssue?.id ?? null}
          onSelect={handleSelectIssue}
          onAccept={handleAccept}
          onDismiss={handleDismiss}
          emptyMessage={emptyMessage}
        />
      </div>

      <SnapshotViewer
        snapshotId={snapshotId}
        highlightedParagraphId={selectedIssue?.paragraph_id ?? null}
      />
    </div>
  );
};

export default App;
