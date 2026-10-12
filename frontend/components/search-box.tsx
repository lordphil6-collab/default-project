"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";

export function SearchBox() {
  const router = useRouter();
  const [q, setQ] = useState("");
  return (
    <form
      role="search"
      style={{ flex: 1, maxWidth: 420, display: "flex" }}
      onSubmit={(e) => {
        e.preventDefault();
        router.push(q.trim() ? `/situations?q=${encodeURIComponent(q.trim())}` : "/situations");
      }}
    >
      <input
        aria-label="Global search"
        placeholder="Search situations, customers, RFQs…"
        value={q}
        onChange={(e) => setQ(e.target.value)}
        style={{ flex: 1 }}
      />
    </form>
  );
}
