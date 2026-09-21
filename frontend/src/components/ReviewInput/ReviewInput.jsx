import React, { useState } from "react";
import SingleReview from "./SingleReview";
import BatchReview from "./BatchReview";

export default function ReviewInput() {
  const [mode, setMode] = useState("single");

  return (
    <div className="space-y-6">
      <div>
        <p className="font-mono text-xs uppercase tracking-widest2 text-moss-dark">
          ✦ Live inference
        </p>
        <h1 className="font-display text-3xl text-ink md:text-4xl">
          What is this review <span className="brand-text italic">really</span> saying?
        </h1>
        <p className="mt-1 max-w-xl text-sm text-ink-soft">
          Drop in a single review, paste a batch, or upload a CSV — CogniSent's CNN model
          reads between the lines.
        </p>
      </div>

      <div className="flex w-fit rounded-full border border-teal-light/60 bg-beige-soft p-1 shadow-card">
        {["single", "batch"].map((m) => (
          <button
            key={m}
            onClick={() => setMode(m)}
            className={`rounded-full px-5 py-2 text-sm font-medium capitalize transition-colors ${
              mode === m ? "bg-teal text-beige-soft" : "text-ink-soft hover:text-ink"
            }`}
          >
            {m}
          </button>
        ))}
      </div>

      {mode === "single" ? <SingleReview /> : <BatchReview />}
    </div>
  );
}
