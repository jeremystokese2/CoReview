import * as React from "react";
import {
  Badge,
  Button,
  Textarea,
  makeStyles,
  tokens,
  Tooltip,
} from "@fluentui/react-components";
import type { Issue, Severity } from "../types";

const useStyles = makeStyles({
  card: {
    display: "flex",
    flexDirection: "column",
    gap: "8px",
    padding: "10px 12px",
    borderTop: `1px solid ${tokens.colorNeutralStroke2}`,
    cursor: "pointer",
    backgroundColor: tokens.colorNeutralBackground1,
  },
  selected: {
    backgroundColor: tokens.colorBrandBackground2,
  },
  resolved: {
    opacity: 0.55,
  },
  head: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: "8px",
  },
  badges: {
    display: "flex",
    gap: "6px",
    alignItems: "center",
    flexWrap: "wrap",
  },
  anchor: {
    fontStyle: "italic",
    borderLeft: `3px solid ${tokens.colorBrandStroke1}`,
    paddingLeft: "8px",
    color: tokens.colorNeutralForeground2,
    fontSize: tokens.fontSizeBase300,
  },
  body: {
    fontSize: tokens.fontSizeBase300,
    color: tokens.colorNeutralForeground1,
  },
  label: {
    fontSize: tokens.fontSizeBase200,
    fontWeight: tokens.fontWeightSemibold,
    color: tokens.colorNeutralForeground3,
    textTransform: "uppercase",
    letterSpacing: "0.04em",
    marginTop: "4px",
  },
  citations: {
    display: "flex",
    gap: "4px",
    flexWrap: "wrap",
  },
  actions: {
    display: "flex",
    gap: "6px",
    marginTop: "4px",
  },
  dismissForm: {
    display: "flex",
    flexDirection: "column",
    gap: "6px",
    marginTop: "4px",
  },
  status: {
    fontSize: tokens.fontSizeBase200,
    color: tokens.colorNeutralForeground3,
  },
  confidence: {
    fontSize: tokens.fontSizeBase100,
    color: tokens.colorNeutralForeground3,
  },
});

function severityColor(s: Severity): "danger" | "warning" | "informative" {
  if (s === "high") return "danger";
  if (s === "medium") return "warning";
  return "informative";
}

export interface IssueCardProps {
  issue: Issue;
  selected: boolean;
  onSelect: (issue: Issue) => void;
  onAccept: (issue: Issue) => void | Promise<void>;
  onDismiss: (issue: Issue, reason: string) => void | Promise<void>;
}

const IssueCard: React.FC<IssueCardProps> = ({
  issue,
  selected,
  onSelect,
  onAccept,
  onDismiss,
}) => {
  const styles = useStyles();
  const [dismissOpen, setDismissOpen] = React.useState(false);
  const [reason, setReason] = React.useState("");
  const [busy, setBusy] = React.useState(false);

  const resolved = issue.status !== "open";
  const classes = [
    styles.card,
    selected ? styles.selected : "",
    resolved ? styles.resolved : "",
  ].join(" ");

  const handleAccept = async (e: React.MouseEvent) => {
    e.stopPropagation();
    setBusy(true);
    try {
      await onAccept(issue);
    } finally {
      setBusy(false);
    }
  };

  const handleDismissSubmit = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!reason.trim()) return;
    setBusy(true);
    try {
      await onDismiss(issue, reason.trim());
      setDismissOpen(false);
      setReason("");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div
      className={classes}
      onClick={() => onSelect(issue)}
      role="button"
      tabIndex={0}
    >
      <div className={styles.head}>
        <div className={styles.badges}>
          <Badge appearance="filled" color={severityColor(issue.severity)}>
            {issue.severity}
          </Badge>
          <Tooltip content={`Confidence ${(issue.confidence * 100).toFixed(0)}%`} relationship="label">
            <span className={styles.confidence}>
              {(issue.confidence * 100).toFixed(0)}%
            </span>
          </Tooltip>
        </div>
        {resolved && (
          <span className={styles.status}>
            {issue.status === "accepted" ? "Accepted" : "Dismissed"}
          </span>
        )}
      </div>

      <div className={styles.anchor}>"{issue.anchor_text}"</div>

      <div className={styles.label}>Why</div>
      <div className={styles.body}>{issue.explanation}</div>

      <div className={styles.label}>Consider</div>
      <div className={styles.body}>{issue.guidance}</div>

      {issue.citations.length > 0 && (
        <div className={styles.citations}>
          {issue.citations.map((c) => (
            <Badge
              key={c.rule_id}
              appearance="outline"
              shape="rounded"
              color="subtle"
            >
              {c.rule_title}
            </Badge>
          ))}
        </div>
      )}

      {issue.status === "dismissed" && issue.dismissal_reason && (
        <>
          <div className={styles.label}>Dismissed because</div>
          <div className={styles.body}>{issue.dismissal_reason}</div>
        </>
      )}

      {!resolved && !dismissOpen && (
        <div className={styles.actions}>
          <Button
            size="small"
            appearance="primary"
            onClick={handleAccept}
            disabled={busy}
          >
            Accept
          </Button>
          <Button
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              setDismissOpen(true);
            }}
            disabled={busy}
          >
            Dismiss
          </Button>
        </div>
      )}

      {!resolved && dismissOpen && (
        <div className={styles.dismissForm} onClick={(e) => e.stopPropagation()}>
          <Textarea
            value={reason}
            onChange={(_, data) => setReason(data.value)}
            placeholder="Why doesn't this apply?"
            rows={2}
          />
          <div className={styles.actions}>
            <Button
              size="small"
              appearance="primary"
              disabled={busy || !reason.trim()}
              onClick={handleDismissSubmit}
            >
              Submit
            </Button>
            <Button
              size="small"
              onClick={() => {
                setDismissOpen(false);
                setReason("");
              }}
              disabled={busy}
            >
              Cancel
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default IssueCard;
