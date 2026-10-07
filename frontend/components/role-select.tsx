"use client";
import { useEffect, useState } from "react";

const ROLES = ["CSR", "Sales", "Ops", "Manager", "Owner"];

export function getRole(): string {
  if (typeof window === "undefined") return "CSR";
  return window.localStorage.getItem("qd-role") || "CSR";
}

// Demo-grade role switch: the header value is what the API enforces.
// Real role management (invite-time roles, server-side checks) lands with user admin.
export function RoleSelect() {
  const [role, setRole] = useState("CSR");
  useEffect(() => {
    setRole(getRole());
  }, []);
  function change(value: string) {
    window.localStorage.setItem("qd-role", value);
    setRole(value);
  }
  return (
    <select aria-label="Acting role" value={role} onChange={(e) => change(e.target.value)} title="Demo role switch — API enforces this header">
      {ROLES.map((r) => (
        <option key={r} value={r}>
          {r}
        </option>
      ))}
    </select>
  );
}
