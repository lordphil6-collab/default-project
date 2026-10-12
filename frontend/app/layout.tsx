import "./globals.css";
import { SessionBar, TrialPill } from "../components/session-bar";
import { Nav } from "../components/nav";
import { SearchBox } from "../components/search-box";

export const metadata = { title: "Freight Customer Service Desk", description: "AI workspace for logistics customer service" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="topbar">
          <b>Freight Customer Service Desk</b>
          <SearchBox />
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
