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
        </div>
      </body>
    </html>
  );
}
