import React from "react";

export default function StatsCard({ label, value, accent = "#4B6B7C", sub }) {
  return (
    <div className="rounded-xl2 border border-teal-light/60 bg-beige-soft p-5 shadow-card">
      <p className="font-mono text-[11px] uppercase tracking-widest2 text-teal-dark">{label}</p>
      <p className="mt-2 font-display text-3xl" style={{ color: accent }}>
        {value}
      </p>
      {sub && <p className="mt-1 text-xs text-ink-faint">{sub}</p>}
    </div>
  );
}
