import * as React from "react";
import { makeStyles, tokens } from "@fluentui/react-components";
import IssueCard from "./IssueCard";
import type { Issue } from "../types";

const useStyles = makeStyles({
  empty: {
    padding: "16px",
    color: tokens.colorNeutralForeground3,
    fontSize: tokens.fontSizeBase300,
  },
  list: {
    display: "flex",
    flexDirection: "column",
    minHeight: 0,
    overflow: "auto",
  },
});

const SEVERITY_RANK: Record<Issue["severity"], number> = {
  high: 0,
  medium: 1,
  low: 2,
};

function paragraphIndex(paragraphId: string): number {
  const m = /^p_(\d+)$/.exec(paragraphId);
  return m ? parseInt(m[1], 10) : Number.MAX_SAFE_INTEGER;
}

function sortIssues(issues: Issue[]): Issue[] {
  return [...issues].sort((a, b) => {
    const rank = SEVERITY_RANK[a.severity] - SEVERITY_RANK[b.severity];
    if (rank !== 0) return rank;
    return paragraphIndex(a.paragraph_id) - paragraphIndex(b.paragraph_id);
  });
}

export interface IssueListProps {
  issues: Issue[];
  selectedIssueId: string | null;
  onSelect: (issue: Issue) => void;
  onAccept: (issue: Issue) => Promise<void> | void;
  onDismiss: (issue: Issue, reason: string) => Promise<void> | void;
  emptyMessage: string;
}

const IssueList: React.FC<IssueListProps> = ({
  issues,
  selectedIssueId,
  onSelect,
  onAccept,
  onDismiss,
  emptyMessage,
}) => {
  const styles = useStyles();
  if (issues.length === 0) {
    return <div className={styles.empty}>{emptyMessage}</div>;
  }
  const sorted = sortIssues(issues);
  return (
    <div className={styles.list}>
      {sorted.map((issue) => (
        <IssueCard
          key={issue.id}
          issue={issue}
          selected={issue.id === selectedIssueId}
          onSelect={onSelect}
          onAccept={onAccept}
          onDismiss={onDismiss}
        />
      ))}
    </div>
  );
};

export default IssueList;
