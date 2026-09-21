import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { getModelInfo, getStats } from "../api/client";

const AppContext = createContext(null);

function generateSessionId() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `sess-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export function AppProvider({ children }) {
  const sessionId = useMemo(() => generateSessionId(), []);
  const [modelInfo, setModelInfo] = useState(null);
  const [stats, setStats] = useState(null);
  const [loadingModel, setLoadingModel] = useState(true);
  const [apiError, setApiError] = useState(null);
  const [refreshFlag, setRefreshFlag] = useState(0);

  const refresh = useCallback(() => setRefreshFlag((f) => f + 1), []);

  useEffect(() => {
    let mounted = true;
    setLoadingModel(true);
    getModelInfo()
      .then((data) => {
        if (!mounted) return;
        setModelInfo(data);
        setApiError(null);
      })
      .catch(() => {
        if (!mounted) return;
        setApiError(
          "Could not reach the sentiment API. Is the backend running on the configured URL?"
        );
      })
      .finally(() => mounted && setLoadingModel(false));
    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    let mounted = true;
    getStats()
      .then((data) => mounted && setStats(data))
      .catch(() => {});
    return () => {
      mounted = false;
    };
  }, [refreshFlag]);

  const value = {
    sessionId,
    modelInfo,
    stats,
    loadingModel,
    apiError,
    refresh,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useAppContext() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useAppContext must be used within an AppProvider");
  return ctx;
}
