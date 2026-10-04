import "./globals.css";

export const metadata = { title: "AI Quotation Desk", description: "Phase 1 design system" };

const NAV = [
  ["Dashboard", "/", true],
  ["Situations", "/", false],
  ["Inbox", "/", false],
  ["RFQs", "/", false],
  ["Comparisons", "/", false],
  ["Quotes", "/", false],
  ["Follow-ups", "/", false],
  ["Exceptions", "/", false],
  ["Design system", "/design-system", false],
] as const;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="topbar">
          <b>AI Quotation Desk</b>
          <input placeholder="Search situations, customers, RFQs…" aria-label="Global search" />
          <span className="pill indigo">Trial: 22 days left</span>
          <span className="pill green">CSR</span>
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
