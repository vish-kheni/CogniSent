import React from "react";
import { useAppContext } from "../../context/AppContext";

export default function Footer() {
  const { apiError } = useAppContext();

  return (
    <footer className="border-t border-teal-light/50 px-6 py-6">
      <div className="mx-auto flex max-w-6xl flex-col items-start justify-between gap-2 text-xs text-ink-soft md:flex-row md:items-center">
        <p className="font-mono">
          <span className="brand-text font-semibold">CogniSent</span> — CNN sentiment analysis,
          with history that sticks around.
        </p>
        <p className={apiError ? "font-medium text-clay-dark" : "text-moss-dark"}>
          {apiError ? apiError : "Connected"} 
        </p>
      </div>
    </footer>
  )
}