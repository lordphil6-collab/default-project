import "./globals.css";
import { SessionBar, TrialPill } from "../components/session-bar";

export const metadata = { title: "AI Quotation Desk", description: "Phase 1 design system" };

const NAV = [
  ["Dashboard", "/", true],
  ["Situations", "/situations", false],
  ["Agents", "/agents", false],
  ["Inbox", "/inbox", false],
  ["Pricing", "/pricing", false],
  ["Billing", "/billing", false],
  ["Follow-ups", "/follow-ups", false],
  ["Exceptions", "/exceptions", false],
  ["Design system", "/design-system", false],
] as const;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="topbar">
          <b>AI Quotation Desk</b>
          <input placeholder="Search situations, customers, RFQs…" aria-label="Global search" />
          <TrialPill />
          <SessionBar />
        </div>
        <div className="shell">
          <nav className="card nav" aria-label="Primary">
            {NAV.map(([label, href, on]) => (
              <a key={label} href={href} className={on ? "on" : ""}>
                {label}
              </a>
            ))}
          </nav>
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>{children}</div>
          <aside style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            <div className="card">
              <h2 style={{ fontSize: 15, margin: "4px 0" }}>Phase 1 scope</h2>
              <p className="muted">Tokens + primitives + domain cards + shell. Full Storybook deferred (see /design-system).</p>
            </div>
          </aside>
        </div>
      </body>
    </html>
  );
}
