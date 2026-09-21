import React, { useState } from "react";
import { Cell, Pie, PieChart, ResponsiveContainer } from "recharts";
import { Eraser, Loader2, Send } from "lucide-react";
import { analyzeReview } from "../../api/client";
import { useAppContext } from "../../context/AppContext";
import { formatPercent, sentimentBadgeClasses, sentimentEmoji } from "../../utils/helpers";

const GAUGE_COLOR = {
  Positive: "#4E9C82",
  Negative: "#C97B5B",
  Neutral: "#D9A441",
};

function ConfidenceGauge({ label, probabilities }) {
  const data = Object.entries(probabilities).map(([name, value]) => ({ name, value }));

  return (
    <div className="relative min-h-[220px] flex-1">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="92%"
            startAngle={180}
            endAngle={0}
            innerRadius="102%"
            outerRadius="150%"
            paddingAngle={2}
            stroke="none"
          >
            {data.map((entry) => (
              <Cell key={entry.name} fill={GAUGE_COLOR[entry.name] || "#94A3A8"} />
            ))}
          </Pie>
        </PieChart>
      </ResponsiveContainer>
      <div className="pointer-events-none absolute inset-x-0 bottom-3 flex flex-col items-center">
        <span className="mt-1 font-mono text-2xl uppercase tracking-widest2 text-teal-dark">
          {sentimentEmoji(label)}
        </span>
        <span className="mt-1 font-mono text-2xl uppercase tracking-widest2 text-teal-dark">
          {label}
        </span>
        <span className="font-display text-xs text-ink">
          {formatPercent(probabilities[label])}
        </span>
      </div>
    </div>
  );
}

export default function SingleReview() {
  const { sessionId, refresh } = useAppContext();
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!text.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await analyzeReview(text.trim(), sessionId);
      setResult(data);
      refresh();
    } catch (err) {
      setError("Analysis failed. Check that the backend API is reachable.");
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setText("");
    setResult(null);
    setError(null);
  };

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
      <div className="flex flex-col lg:col-span-3">
        <div className="mb-2 flex items-center justify-between">
          <label className="font-mono text-[11px] uppercase tracking-widest2 text-teal-dark">
            Review text
          </label>
          {(text || result) && (
            <button
              type="button"
              onClick={handleClear}
              className="flex items-center gap-1.5 text-xs text-ink-faint hover:text-clay-dark"
            >
              <Eraser size={13} />
              Clear
            </button>
          )}
        </div>

        <form
          onSubmit={handleSubmit}
          className="relative flex flex-1 flex-col rounded-xl2 border border-teal-light/60 bg-beige-soft p-6 shadow-card"
        >
          <span
            aria-hidden="true"
            className="pointer-events-none absolute -top-3 left-5 select-none font-display text-6xl italic leading-none text-sky-dark/40"
          >
            "
          </span>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Paste or type a shoe review to analyze..."
            className="w-full flex-1 resize-none rounded-xl2 border border-teal-light/70 bg-beige-soft p-4 text-sm text-ink placeholder:text-ink-faint focus:border-teal"
            style={{ minHeight: "160px" }}
          />

          <div className="mt-5 flex items-center justify-between">
            <p className="font-mono text-xs text-ink-faint">Model: CNN (Conv1D)</p>
            <button
              type="submit"
              disabled={loading || !text.trim()}
              className="flex items-center gap-2 rounded-full bg-teal px-5 py-2.5 text-sm font-semibold text-beige-soft shadow-pop transition-transform hover:-translate-y-0.5 disabled:translate-y-0 disabled:opacity-40"
            >
              {loading ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
              {loading ? "Analyzing" : "Run analysis"}
            </button>
          </div>

          {error && <p className="mt-3 text-sm font-medium text-clay-dark">{error}</p>}
        </form>
      </div>

      <div className="flex flex-col lg:col-span-2">
        <p className="mb-2 font-mono text-[11px] uppercase tracking-widest2 text-teal-dark">
          Result
        </p>

        {!result ? (
          <div className="flex flex-1 flex-col items-center justify-center gap-2 rounded-xl2 border border-dashed border-sky-dark/40 bg-sky-tint/50 p-6 text-center text-sm text-ink-soft">
            <span className="font-display text-2xl text-sky-dark">✦</span>
            Nothing to show yet — run an analysis and I'll tell you what I think.
          </div>
        ) : (
          <div className="flex flex-1 flex-col rounded-xl2 border border-teal-light/60 bg-beige-soft p-5 shadow-card">
            <span
              className={`inline-block w-fit rounded-full border px-3 py-1 text-sm font-semibold ${sentimentBadgeClasses(
                result.label
              )}`}
            >
              {sentimentEmoji(result.label)} {result.label}
            </span>

            <ConfidenceGauge label={result.label} probabilities={result.probabilities} />

            <div className="mt-1 flex justify-center gap-4 text-xs">
              {Object.entries(result.probabilities)
                .sort((a, b) => b[1] - a[1])
                .map(([label, prob]) => (
                  <div key={label} className="flex items-center gap-1.5">
                    <span
                      className="h-2 w-2 rounded-full"
                      style={{ backgroundColor: GAUGE_COLOR[label] || "#94A3A8" }}
                    />
                    <span className="text-ink-soft">
                       {label} {formatPercent(prob)}
                    </span>
                  </div>
                ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
