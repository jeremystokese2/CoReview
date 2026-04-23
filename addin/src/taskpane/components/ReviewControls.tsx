import * as React from "react";
import {
  Button,
  Dropdown,
  Label,
  Option,
  Spinner,
  makeStyles,
  tokens,
} from "@fluentui/react-components";
import type { PackSummary } from "../types";

const useStyles = makeStyles({
  wrap: {
    display: "flex",
    flexDirection: "column",
    gap: "8px",
    padding: "12px 16px",
    borderBottom: `1px solid ${tokens.colorNeutralStroke2}`,
  },
  row: {
    display: "flex",
    gap: "8px",
    alignItems: "end",
  },
  dropdown: {
    flex: 1,
    minWidth: 0,
  },
  hint: {
    fontSize: tokens.fontSizeBase200,
    color: tokens.colorNeutralForeground3,
  },
});

export interface ReviewControlsProps {
  packs: PackSummary[];
  selectedPackId: string | null;
  onSelectPack: (id: string) => void;
  onReview: () => void;
  busy: boolean;
  loadingPacks: boolean;
}

const ReviewControls: React.FC<ReviewControlsProps> = ({
  packs,
  selectedPackId,
  onSelectPack,
  onReview,
  busy,
  loadingPacks,
}) => {
  const styles = useStyles();
  const selected = packs.find((p) => p.id === selectedPackId);

  return (
    <div className={styles.wrap}>
      <div>
        <Label htmlFor="pack-dropdown">Review pack</Label>
        <div className={styles.row}>
          <Dropdown
            id="pack-dropdown"
            className={styles.dropdown}
            placeholder={loadingPacks ? "Loading packs…" : "Select a pack"}
            value={selected?.name ?? ""}
            selectedOptions={selectedPackId ? [selectedPackId] : []}
            onOptionSelect={(_, data) => {
              if (data.optionValue) onSelectPack(data.optionValue);
            }}
            disabled={busy || loadingPacks || packs.length === 0}
          >
            {packs.map((p) => (
              <Option key={p.id} value={p.id} text={p.name}>
                {p.name}
              </Option>
            ))}
          </Dropdown>
          <Button
            appearance="primary"
            onClick={onReview}
            disabled={busy || !selectedPackId}
            icon={busy ? <Spinner size="tiny" /> : undefined}
          >
            {busy ? "Reviewing…" : "Review document"}
          </Button>
        </div>
      </div>
      {selected && <span className={styles.hint}>{selected.description}</span>}
    </div>
  );
};

export default ReviewControls;
