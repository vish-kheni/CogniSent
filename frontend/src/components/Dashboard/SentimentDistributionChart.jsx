import React from "react";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

const COLORS = { Positive: "#4E9C82", Negative: "#C97B5B", Neutral: "#D9A441" };

export default function SentimentDistributionChart({ counts, total }) {
  const data = Object.entries(counts || {}).map(([name, value]) => ({ name, value }));

  return (
    <div className="rounded-xl2 border border-teal-light/60 bg-beige-soft p-5 shadow-card">
      <p className="mb-1 font-mono text-[11px] uppercase tracking-widest2 text-teal-dark">
        Sentiment Distribution
      </p>
      <p className="mb-3 text-xs text-ink-faint">{total} review(s) analyzed in total</p>

      {total === 0 ? (
        <div className="flex h-52 items-center justify-center text-sm text-ink-soft">
          Analyze some reviews to populate this chart.
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={220}>
          <PieChart>
            <Pie
              data={data}
              dataKey="value"
              nameKey="name"
              innerRadius={55}
              outerRadius={85}
              paddingAngle={3}
              stroke="none"
            >
              {data.map((entry) => (
                <Cell key={entry.name} fill={COLORS[entry.name] || "#94A3A8"} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                background: "#FBFAF6",
                border: "1px solid #A9C1CB",
                borderRadius: "0.75rem",
                color: "#2E3A40",
              }}
            />
          </PieChart>
        </ResponsiveContainer>
      )}

      <div className="mt-2 flex justify-center gap-4 text-xs">
        {data.map((d) => (
          <div key={d.name} className="flex items-center gap-1.5">
            <span
              className="h-2 w-2 rounded-full"
              style={{ backgroundColor: COLORS[d.name] || "#94A3A8" }}
            />
            <span className="text-ink-soft">
              {d.name} ({d.value})
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
