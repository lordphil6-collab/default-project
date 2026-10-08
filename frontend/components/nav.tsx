"use client";
import { usePathname } from "next/navigation";

const NAV: [string, string][] = [
  ["Dashboard", "/"],
  ["Situations", "/situations"],
  ["Agents", "/agents"],
  ["Inbox", "/inbox"],
  ["Pricing", "/pricing"],
  ["Billing", "/billing"],
  ["Admin", "/admin"],
  ["Follow-ups", "/follow-ups"],
  ["Exceptions", "/exceptions"],
  ["Design system", "/design-system"],
];

export function Nav() {
  const path = usePathname();
  const active = (href: string) => (href === "/" ? path === "/" : path === href || path.startsWith(href + "/"));
  return (
    <nav className="card nav" aria-label="Primary">
      {NAV.map(([label, href]) => (
        <a key={label} href={href} className={active(href) ? "on" : ""} aria-current={active(href) ? "page" : undefined}>
          {label}
        </a>
      ))}
    </nav>
  );
}
