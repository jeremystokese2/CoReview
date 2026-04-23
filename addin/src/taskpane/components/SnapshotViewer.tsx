import * as React from "react";
import { makeStyles, tokens, Spinner } from "@fluentui/react-components";
import { snapshotHtmlUrl } from "../services/api";

const HIGHLIGHT_CLASS = "co-review-highlighted";

const useStyles = makeStyles({
  wrap: {
    display: "flex",
    flexDirection: "column",
    minHeight: 0,
    flex: 1,
    borderTop: `1px solid ${tokens.colorNeutralStroke2}`,
  },
  head: {
    padding: "8px 16px",
    fontSize: tokens.fontSizeBase200,
    fontWeight: tokens.fontWeightSemibold,
    color: tokens.colorNeutralForeground3,
    textTransform: "uppercase",
    letterSpacing: "0.04em",
    backgroundColor: tokens.colorNeutralBackground2,
  },
  body: {
    flex: 1,
    overflow: "auto",
    padding: "12px 16px",
    fontSize: tokens.fontSizeBase300,
    color: tokens.colorNeutralForeground1,
    "& h1, & h2, & h3, & h4, & h5, & h6": {
      margin: "10px 0 6px",
    },
    "& p": {
      margin: "0 0 8px",
    },
    [`& .${HIGHLIGHT_CLASS}`]: {
      backgroundColor: tokens.colorPaletteYellowBackground2,
      transition: "background-color 300ms ease",
      borderRadius: "3px",
    },
  },
  loading: {
    padding: "16px",
    color: tokens.colorNeutralForeground3,
  },
  error: {
    padding: "16px",
    color: tokens.colorPaletteRedForeground1,
  },
});

export interface SnapshotViewerProps {
  snapshotId: string | null;
  highlightedParagraphId: string | null;
}

const SnapshotViewer: React.FC<SnapshotViewerProps> = ({
  snapshotId,
  highlightedParagraphId,
}) => {
  const styles = useStyles();
  const [html, setHtml] = React.useState<string>("");
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const bodyRef = React.useRef<HTMLDivElement | null>(null);

  // Fetch the snapshot HTML whenever the snapshotId changes.
  React.useEffect(() => {
    if (!snapshotId) {
      setHtml("");
      setError(null);
      return undefined;
    }
    const ctrl = new AbortController();
    setLoading(true);
    setError(null);
    fetch(snapshotHtmlUrl(snapshotId), { signal: ctrl.signal })
      .then(async (res) => {
        if (!res.ok) throw new Error(`Snapshot fetch failed: ${res.status}`);
        return res.text();
      })
      .then((text) => setHtml(text))
      .catch((e: any) => {
        if (e?.name !== "AbortError") setError(e?.message ?? String(e));
      })
      .finally(() => setLoading(false));
    return () => ctrl.abort();
  }, [snapshotId]);

  // Apply the highlight when either the HTML or the target paragraph changes.
  React.useEffect(() => {
    const root = bodyRef.current;
    if (!root) return;
    root.querySelectorAll(`.${HIGHLIGHT_CLASS}`).forEach((el) =>
      el.classList.remove(HIGHLIGHT_CLASS)
    );
    if (!highlightedParagraphId) return;
    const target = root.querySelector(
      `[data-rid="${cssEscape(highlightedParagraphId)}"]`
    ) as HTMLElement | null;
    if (target) {
      target.classList.add(HIGHLIGHT_CLASS);
      target.scrollIntoView({ block: "center", behavior: "smooth" });
    }
  }, [html, highlightedParagraphId]);

  if (!snapshotId) {
    return null;
  }

  return (
    <section className={styles.wrap}>
      <div className={styles.head}>Snapshot</div>
      {loading && (
        <div className={styles.loading}>
          <Spinner size="tiny" label="Loading snapshot…" />
        </div>
      )}
      {error && <div className={styles.error}>{error}</div>}
      {!loading && !error && (
        <div
          ref={bodyRef}
          className={styles.body}
          // The snapshot HTML is produced by our own server-side normaliser
          // which strips <script>/<style>/event handlers. Still rendered in a
          // sandboxed-by-convention way — do not mutate this HTML at render.
          dangerouslySetInnerHTML={{ __html: html }}
        />
      )}
    </section>
  );
};

function cssEscape(v: string): string {
  // Minimal escape — our paragraph ids are always `p_<int>`, so this is safe
  // but we still defensively escape double quotes.
  return v.replace(/"/g, '\\"');
}

export default SnapshotViewer;
