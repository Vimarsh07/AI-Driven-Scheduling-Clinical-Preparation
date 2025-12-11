import React from "react";

type Props = {
  level: "low" | "medium" | "high";
  score: number;
};

const colors: Record<"low" | "medium" | "high", string> = {
  low: "#16a34a",
  medium: "#f59e0b",
  high: "#dc2626",
};

export const RiskBadge: React.FC<Props> = ({ level, score }) => {
  return (
    <span
      style={{
        backgroundColor: `${colors[level]}20`,
        color: colors[level],
        padding: "4px 8px",
        borderRadius: "999px",
        fontSize: "0.8rem",
        fontWeight: 600,
      }}
    >
      Risk: {level.toUpperCase()} ({score})
    </span>
  );
};
