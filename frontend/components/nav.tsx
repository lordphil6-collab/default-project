"use client";
import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";

const NAV: [string, string][] = [
  ["Dashboard", "/"],
  ["Get quote", "/quote"],
  ["Situations", "/situations"],
  ["Agents", "/agents"],
  ["Inbox", "/inbox"],
  ["Pricing", "/pricing"],
  ["Billing", "/billing"],
  ["Team", "/team"],
  ["Mailbox", "/settings/mailbox"],
  ["Admin", "/admin"],
  ["Follow-ups", "/follow-ups"],
  ["Exceptions", "/exceptions"],
  ["Design system", "/design-system"],
];

type Counts = { follow_ups: number; exceptions: number };

export function Nav() {
  const path = usePathname();
  const [counts, setCounts] = useState<Counts | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const tok = await fetch("/api/auth/token");
        if (!tok.ok) return;
        const { token } = (await tok.json()) as { token?: string };
        if (!token) return;
        const s = await fetch("/api/auth/get-session");
        const orgId = ((await s.json()) as { session?: { activeOrganizationId?: string } | null })
          ?.session?.activeOrganizationId;
        if (!orgId) return;
        const r = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/dashboard/today`,
          { headers: { Authorization: `Bearer ${token}`, "X-Org-Id": orgId, "X-Role": "CSR" } }
        );
        if (r.ok) {
          const c = (await r.json()) as Counts;
          setCounts({ follow_ups: c.follow_ups || 0, exceptions: c.exceptions || 0 });
        }
      } catch {
        // Logged out or API down — plain nav, no badges.
      }
    })();
  }, [path]);

  const badge = (href: string): number => {
    if (!counts) return 0;
    if (href === "/follow-ups") return counts.follow_ups;
    if (href === "/exceptions") return counts.exceptions;
    return 0;
  };

  const active = (href: string) => (href === "/" ? path === "/" : path === href || path.startsWith(href + "/"));
  return (
    <nav className="card nav" aria-label="Primary">
      {NAV.map(([label, href]) => (
        <a key={label} href={href} className={active(href) ? "on" : ""} aria-current={active(href) ? "page" : undefined}>
          {label}
          {badge(href) > 0 ? <span className="pill red" style={{ marginLeft: 6 }}>{badge(href)}</span> : null}
        </a>
      ))}
    </nav>
  );
}
