import React from "react";
import { Gauge, Zap } from "lucide-react";

const TABS = [
  { id: "analyze", label: "Analyze", icon: Zap },
  { id: "dashboard", label: "Dashboard", icon: Gauge },
];

export default function Navbar({ activeTab, onTabChange }) {
  return (
    <header className="sticky top-0 z-30 border-b border-teal-light/50 bg-beige-soft/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="group flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-brand-glow shadow-pop transition-transform duration-300 hover:-rotate-6 hover:scale-105">
            <span className="font-display text-lg font-semibold italic leading-none text-beige-soft">
              C·S
            </span>
          </div>
          <div className="leading-tight">
            <p className="font-display text-xl tracking-tight text-ink">
              Cogni<span className="brand-text font-semibold">Sent</span>
            </p>
            <p className="font-mono text-[10px] uppercase tracking-widest2 text-teal-dark">
              sentiment, understood
            </p>
          </div>
        </div>

        <nav className="flex gap-1.5">
          {TABS.map(({ id, label, icon: Icon }) => {
            const active = activeTab === id;
            return (
              <button
                key={id}
                onClick={() => onTabChange(id)}
                className={`flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium transition-colors ${
                  active
                    ? "bg-teal text-beige-soft shadow-pop"
                    : "text-ink-soft hover:bg-sky-tint hover:text-ink"
                }`}
              >
                <Icon size={15} />
                {label}
              </button>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
