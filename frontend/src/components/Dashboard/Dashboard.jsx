import React, { useState } from "react";
import { Trash2 } from "lucide-react";
import { clearReviews } from "../../api/client";
import { useAppContext } from "../../context/AppContext";
import ConfirmModal from "../Layout/ConfirmModal";
import StatsCard from "./StatsCard";
import SentimentDistributionChart from "./SentimentDistributionChart";
import SessionList from "./SessionList";

export default function Dashboard({ onNavigate }) {
  const { stats, refresh } = useAppContext();
  const [confirmOpen, setConfirmOpen] = useState(false);

  const total = stats?.total_reviews ?? 0;
  const counts = stats?.sentiment_counts ?? { Positive: 0, Negative: 0, Neutral: 0 };

  const handleConfirmClearAll = async () => {
    setConfirmOpen(false);
    await clearReviews();
    refresh();
  };

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="font-mono text-xs uppercase tracking-widest2 text-moss-dark">
            ✦ At a glance
          </p>
          <h1 className="font-display text-3xl text-ink md:text-4xl">Sentiment Dashboard</h1>
          <p className="mt-1 max-w-xl text-sm text-ink-soft">
            A running tally of everything CogniSent has ever analyzed for you — persisted, not
            just remembered for the moment.
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setConfirmOpen(true)}
            disabled={total === 0}
            className="flex items-center gap-2 rounded-full border border-clay/40 bg-clay-tint px-4 py-2 text-sm text-clay-dark hover:bg-clay-light/60 disabled:opacity-40"
          >
            <Trash2 size={14} /> Clear all history
          </button>
          <button
            onClick={() => onNavigate("analyze")}
            className="w-fit rounded-full bg-teal px-5 py-2.5 text-sm font-semibold text-beige-soft shadow-pop transition-transform hover:-translate-y-0.5"
          >
            Analyze a review →
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatsCard label="Total Reviews" value={total} accent="#4B6B7C" />
        <StatsCard label="Positive" value={counts.Positive || 0} accent="#4E9C82" />
        <StatsCard label="Negative" value={counts.Negative || 0} accent="#C97B5B" />
        <StatsCard label="Neutral" value={counts.Neutral || 0} accent="#D9A441" />
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <div className="md:col-span-1">
          <SentimentDistributionChart counts={counts} total={total} />
        </div>

        <div className="md:col-span-2">
          <p className="mb-2 font-mono text-[11px] uppercase tracking-widest2 text-teal-dark">
            History by Session
          </p>
          <SessionList refreshKey={stats} />
        </div>
      </div>

      <ConfirmModal
        open={confirmOpen}
        title="Clear all history?"
        message="This permanently deletes every saved review across all sessions. This can't be undone."
        confirmLabel="Clear everything"
        onConfirm={handleConfirmClearAll}
        onCancel={() => setConfirmOpen(false)}
      />
    </div>
  );
}
