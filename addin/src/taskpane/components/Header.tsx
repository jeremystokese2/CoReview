import * as React from "react";
import { makeStyles, tokens } from "@fluentui/react-components";

const useStyles = makeStyles({
  header: {
    display: "flex",
    flexDirection: "column",
    padding: "12px 16px",
    borderBottom: `1px solid ${tokens.colorNeutralStroke2}`,
    backgroundColor: tokens.colorNeutralBackground2,
  },
  title: {
    fontSize: tokens.fontSizeBase500,
    fontWeight: tokens.fontWeightSemibold,
    margin: 0,
    color: tokens.colorNeutralForeground1,
  },
  subtitle: {
    fontSize: tokens.fontSizeBase200,
    color: tokens.colorNeutralForeground3,
    marginTop: "2px",
  },
});

const Header: React.FC = () => {
  const styles = useStyles();
  return (
    <header className={styles.header}>
      <h1 className={styles.title}>Drafting Assistant</h1>
      <span className={styles.subtitle}>Review your draft against a style or policy pack.</span>
    </header>
  );
};

export default Header;
