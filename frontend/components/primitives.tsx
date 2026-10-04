import React from "react";

type PillTone = "default" | "amber" | "green" | "red" | "indigo";

export function StatusPill({ tone = "default", children }: { tone?: PillTone; children: React.ReactNode }) {
  const cls = tone === "default" ? "pill" : `pill ${tone}`;
  return <span className={cls}>{children}</span>;
}

export function Card({ title, children }: { title?: string; children: React.ReactNode }) {
  return (
    <div className="card">
      {title ? <h2 style={{ fontSize: 15, margin: "4px 0 8px" }}>{title}</h2> : null}
      {children}
    </div>
  );
}

export function ActionButton({
  secondary,
  children,
  onClick,
}: {
  secondary?: boolean;
  children: React.ReactNode;
  onClick?: () => void;
}) {
  return (
    <button className={secondary ? "btn sec" : "btn"} onClick={onClick} type="button">
      {children}
    </button>
  );
}
