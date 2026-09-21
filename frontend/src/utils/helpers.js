export function sentimentEmoji(label) {
  switch ((label || "").toLowerCase()) {
    case "positive":
      return "😊";
    case "negative":
      return "😞";
    case "neutral":
      return "😐";
    default:
      return "🤔";
  }
}

export function sentimentColor(label) {
  switch ((label || "").toLowerCase()) {
    case "positive":
      return "#4E9C82";
    case "negative":
      return "#C97B5B";
    case "neutral":
      return "#D9A441";
    default:
      return "#94A3A8";
  }
}

export function sentimentBadgeClasses(label) {
  switch ((label || "").toLowerCase()) {
    case "positive":
      return "bg-moss-tint text-moss-dark border-moss-light";
    case "negative":
      return "bg-clay-tint text-clay-dark border-clay-light";
    case "neutral":
      return "bg-amber-tint text-amber-dark border-amber-light";
    default:
      return "bg-ink/5 text-ink-soft border-ink/10";
  }
}

export function formatPercent(value, digits = 1) {
  if (value === null || value === undefined || isNaN(value)) return "—";
  return `${(value * 100).toFixed(digits)}%`;
}

export function formatTimestamp(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatTimeOnly(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
}

export function formatDateOnly(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
}

export function truncate(text, max = 140) {
  if (!text) return "";
  return text.length > max ? `${text.slice(0, max).trim()}…` : text;
}
