import React, { useEffect, useState } from "react";
import { ChevronDown, ChevronUp, Trash2 } from "lucide-react";
import { deleteReview, deleteSession, getReviews, getSessions } from "../../api/client";
import { useAppContext } from "../../context/AppContext";
import ConfirmModal from "../Layout/ConfirmModal";
import {
  formatDateOnly,
  formatPercent,
  formatTimeOnly,
  sentimentBadgeClasses,
  truncate,
} from "../../utils/helpers";

function SessionReviews({ sessionId, onSessionEmptied }) {
  const { refresh } = useAppContext();
  const [reviews, setReviews] = useState(null);
  const [pendingDeleteId, setPendingDeleteId] = useState(null);

  const load = () => {
    getReviews({ session_id: sessionId, limit: 100 }).then((data) => setReviews(data.items));
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId]);

  const handleConfirmDelete = async () => {
    const id = pendingDeleteId;
    setPendingDeleteId(null);
    await deleteReview(id);
    refresh();
    const remaining = (reviews || []).filter((r) => r.id !== id);
    setReviews(remaining);
    if (remaining.length === 0) onSessionEmptied?.();
  };

  if (!reviews) {
    return <div className="px-4 py-4 text-sm text-ink-faint">Loading reviews…</div>;
  }

  return (
    <>
      <div className="divide-y divide-teal-light/40 border-t border-teal-light/50 bg-sky-tint/40">
        {reviews.map((r) => (
          <div key={r.id} className="flex items-start justify-between gap-3 px-4 py-3">
            <div className="min-w-0">
              <p className="text-sm text-ink">{truncate(r.review, 130)}</p>
              <p className="mt-1 font-mono text-[11px] text-ink-faint">
                {formatTimeOnly(r.created_at)}
              </p>
            </div>
            <div className="flex shrink-0 items-center gap-2">
              <span
                className={`rounded-full border px-2 py-1 text-[11px] font-medium ${sentimentBadgeClasses(
                  r.label
                )}`}
              >
                {r.label} · {formatPercent(r.confidence)}
              </span>
              <button
                onClick={() => setPendingDeleteId(r.id)}
                title="Delete this review"
                className="text-ink-faint hover:text-clay-dark"
              >
                <Trash2 size={14} />
              </button>
            </div>
          </div>
        ))}
      </div>

      <ConfirmModal
        open={pendingDeleteId !== null}
        title="Delete this review?"
        message="This permanently removes it from your history. This can't be undone."
        confirmLabel="Delete"
        onConfirm={handleConfirmDelete}
        onCancel={() => setPendingDeleteId(null)}
      />
    </>
  );
}

export default function SessionList({ refreshKey }) {
  const { refresh } = useAppContext();
  const [sessions, setSessions] = useState(null);
  const [expanded, setExpanded] = useState(null);
  const [pendingDeleteSession, setPendingDeleteSession] = useState(null);

  const loadSessions = () => {
    getSessions(20).then((data) => setSessions(data));
  };

  useEffect(() => {
    loadSessions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshKey]);

  const handleConfirmDeleteSession = async () => {
    const sessionId = pendingDeleteSession;
    setPendingDeleteSession(null);
    await deleteSession(sessionId);
    if (expanded === sessionId) setExpanded(null);
    refresh();
    loadSessions();
  };

  if (sessions === null) {
    return (
      <div className="rounded-xl2 border border-teal-light/60 bg-beige-soft p-8 text-center text-sm text-ink-soft shadow-card">
        Loading sessions…
      </div>
    );
  }

  if (sessions.length === 0) {
    return (
      <div className="rounded-xl2 border border-dashed border-sky-dark/40 bg-sky-tint/40 p-8 text-center text-sm text-ink-soft">
        No sessions yet. Analyze a review to start your first one.
      </div>
    );
  }

  return (
    <>
      <div className="overflow-hidden rounded-xl2 border border-teal-light/60 bg-beige-soft shadow-card">
        {sessions.map((s, idx) => {
          const isOpen = expanded === s.session_id;
          return (
            <div key={s.session_id} className={idx > 0 ? "border-t border-teal-light/50" : ""}>
              <div className="flex w-full items-center justify-between gap-3 px-4 py-3.5 hover:bg-sky-tint/30">
                <button
                  onClick={() => setExpanded(isOpen ? null : s.session_id)}
                  className="flex min-w-0 flex-1 items-center justify-between gap-4 text-left"
                >
                  <div className="min-w-0">
                    <p className="font-medium text-ink">
                      Session · {formatDateOnly(s.started_at)}
                    </p>
                    <p className="font-mono text-[11px] text-ink-faint">
                      {formatTimeOnly(s.started_at)} – {formatTimeOnly(s.last_activity_at)} ·{" "}
                      {s.total} review(s)
                    </p>
                  </div>
                  <div className="hidden shrink-0 gap-2 sm:flex">
                    {s.sentiment_counts.Positive > 0 && (
                      <span className="rounded-full border border-moss-light bg-moss-tint px-2 py-0.5 text-[11px] text-moss-dark">
                        +{s.sentiment_counts.Positive}
                      </span>
                    )}
                    {s.sentiment_counts.Negative > 0 && (
                      <span className="rounded-full border border-clay-light bg-clay-tint px-2 py-0.5 text-[11px] text-clay-dark">
                        −{s.sentiment_counts.Negative}
                      </span>
                    )}
                    {s.sentiment_counts.Neutral > 0 && (
                      <span className="rounded-full border border-amber-light bg-amber-tint px-2 py-0.5 text-[11px] text-amber-dark">
                        ~{s.sentiment_counts.Neutral}
                      </span>
                    )}
                  </div>
                </button>
                <button
                  onClick={() => setPendingDeleteSession(s.session_id)}
                  title="Delete this session"
                  className="shrink-0 text-ink-faint hover:text-clay-dark"
                >
                  <Trash2 size={15} />
                </button>
                <button
                  onClick={() => setExpanded(isOpen ? null : s.session_id)}
                  className="shrink-0 text-ink-faint"
                >
                  {isOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                </button>
              </div>
              {isOpen && (
                <SessionReviews
                  sessionId={s.session_id}
                  onSessionEmptied={() => {
                    setExpanded(null);
                    loadSessions();
                  }}
                />
              )}
            </div>
          );
        })}
      </div>

      <ConfirmModal
        open={pendingDeleteSession !== null}
        title="Delete this entire session?"
        message="This permanently removes every review analyzed during this session. This can't be undone."
        confirmLabel="Delete session"
        onConfirm={handleConfirmDeleteSession}
        onCancel={() => setPendingDeleteSession(null)}
      />
    </>
  );
}
