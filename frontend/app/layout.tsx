import "./globals.css";
import { SessionBar, TrialPill } from "../components/session-bar";
import { Nav } from "../components/nav";

export const metadata = { title: "AI Quotation Desk", description: "Phase 1 design system" };

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
          <Nav />
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
