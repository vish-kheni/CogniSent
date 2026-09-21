import React, { useState } from "react";
import Papa from "papaparse";
import * as XLSX from "xlsx";
import { Eraser, FileSpreadsheet, Loader2, UploadCloud } from "lucide-react";
import { analyzeBatch } from "../../api/client";
import { useAppContext } from "../../context/AppContext";
import { formatPercent, sentimentBadgeClasses, truncate } from "../../utils/helpers";

const REVIEW_COLUMN_HINTS = ["review", "text", "comment", "feedback", "message"];

function extractReviewColumn(fields) {
  if (!fields || fields.length === 0) return null;
  const lower = fields.map((f) => f.toLowerCase());
  for (const hint of REVIEW_COLUMN_HINTS) {
    const idx = lower.findIndex((f) => f.includes(hint));
    if (idx !== -1) return fields[idx];
  }
  return fields[0];
}

function extractTextsFromRows(rows) {
  const fields = rows.length > 0 ? Object.keys(rows[0]) : [];
  const column = extractReviewColumn(fields);
  if (!column) return { texts: [], column: null };
  const texts = rows.map((row) => (row[column] ?? "").toString().trim()).filter(Boolean);
  return { texts, column };
}

export default function BatchReview() {
  const { sessionId, refresh } = useAppContext();
  const [raw, setRaw] = useState("");
  const [fileName, setFileName] = useState(null);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [error, setError] = useState(null);

  const lineCount = raw.split("\n").map((l) => l.trim()).filter(Boolean).length;

  const handleFile = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setFileName(file.name);
    setError(null);

    const lowerName = file.name.toLowerCase();

    if (lowerName.endsWith(".csv")) {
      Papa.parse(file, {
        header: true,
        skipEmptyLines: true,
        complete: (results) => {
          const { texts, column } = extractTextsFromRows(results.data);
          if (!column) {
            setError("Couldn't find a usable column in that CSV.");
            return;
          }
          if (texts.length === 0) {
            setError("That CSV didn't have any review text CogniSent could read.");
            return;
          }
          setRaw(texts.join("\n"));
        },
        error: () => setError("Failed to parse that CSV file."),
      });
    } else if (lowerName.endsWith(".xlsx") || lowerName.endsWith(".xls")) {
      file
        .arrayBuffer()
        .then((buffer) => {
          const workbook = XLSX.read(buffer, { type: "array" });
          const firstSheetName = workbook.SheetNames[0];
          const sheet = workbook.Sheets[firstSheetName];
          const rows = XLSX.utils.sheet_to_json(sheet, { defval: "" });

          const { texts, column } = extractTextsFromRows(rows);
          if (!column) {
            setError("Couldn't find a usable column in that spreadsheet.");
            return;
          }
          if (texts.length === 0) {
            setError("That spreadsheet didn't have any review text CogniSent could read.");
            return;
          }
          setRaw(texts.join("\n"));
        })
        .catch(() => setError("Failed to parse that Excel file."));
    } else {
      setError("Please upload a .csv or .xlsx/.xls file.");
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const texts = raw
      .split("\n")
      .map((l) => l.trim())
      .filter(Boolean);
    if (texts.length === 0) return;

    setLoading(true);
    setError(null);
    try {
      const data = await analyzeBatch(texts, sessionId);
      setResults(data);
      refresh();
    } catch (err) {
      setError("Batch analysis failed. Check that the backend API is reachable.");
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setRaw("");
    setFileName(null);
    setResults([]);
    setError(null);
  };

  return (
    <div className="space-y-6">
      <form
        onSubmit={handleSubmit}
        className="rounded-xl2 border border-teal-light/60 bg-beige-soft p-6 shadow-card"
      >
        <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
          <label className="font-mono text-[11px] uppercase tracking-widest2 text-teal-dark">
            One review per line
          </label>
          <div className="flex items-center gap-4">
            {(raw || results.length > 0) && (
              <button
                type="button"
                onClick={handleClear}
                className="flex items-center gap-1.5 text-xs text-ink-faint hover:text-clay-dark"
              >
                <Eraser size={13} />
                Clear
              </button>
            )}
            <label className="flex cursor-pointer items-center gap-1.5 text-xs text-ink-soft hover:text-teal-dark">
              <UploadCloud size={14} />
              Upload .csv or .xlsx
              <input
                type="file"
                accept=".csv,.xlsx,.xls"
                className="hidden"
                onChange={handleFile}
              />
            </label>
          </div>
        </div>

        {fileName && (
          <div className="mb-2 flex items-center gap-1.5 text-xs text-moss-dark">
            <FileSpreadsheet size={13} />
            Loaded <span className="font-medium">{fileName}</span> — {lineCount} review(s) found
          </div>
        )}

        <textarea
          value={raw}
          onChange={(e) => setRaw(e.target.value)}
          rows={8}
          placeholder={"Great shoe, super comfortable...\nSole fell apart within a month...\nIt's okay, nothing special..."}
          className="w-full resize-none rounded-xl2 border border-teal-light/70 bg-beige-soft p-4 font-mono text-sm text-ink placeholder:text-ink-faint focus:border-teal"
        />

        <p className="mt-1.5 text-xs text-ink-faint">
          CSV and Excel uploads auto-detect a review/text/comment column. No matching header?
          We'll use the first column.<br />
          Data limit is 100 reviews per batch.
        </p>

        <div className="mt-4 flex items-center justify-between">
          <p className="font-mono text-xs text-ink-faint">{lineCount} review(s) queued</p>
          <button
            type="submit"
            disabled={loading || lineCount === 0}
            className="flex items-center gap-2 rounded-full bg-teal px-5 py-2.5 text-sm font-semibold text-beige-soft shadow-pop disabled:opacity-40"
          >
            {loading && <Loader2 size={16} className="animate-spin" />}
            {loading ? "Analyzing batch" : `Analyze ${lineCount || ""} reviews`}
          </button>
        </div>
        {error && <p className="mt-3 text-sm font-medium text-clay-dark">{error}</p>}
      </form>

      {results.length > 0 && (
        <div className="overflow-hidden rounded-xl2 border border-teal-light/60 bg-beige-soft shadow-card">
          <div className="grid grid-cols-12 gap-2 border-b border-teal-light/50 bg-sky-tint px-4 py-3 font-mono text-[11px] uppercase tracking-widest2 text-teal-dark">
            <span className="col-span-7">Review</span>
            <span className="col-span-3">Sentiment</span>
            <span className="col-span-2 text-right">Confidence</span>
          </div>
          <div className="max-h-96 divide-y divide-teal-light/40 overflow-y-auto scrollbar-thin">
            {results.map((r) => (
              <div key={r.id} className="grid grid-cols-12 items-center gap-2 px-4 py-3 text-sm">
                <span className="col-span-7 text-ink">{truncate(r.review, 90)}</span>
                <span className="col-span-3">
                  <span
                    className={`rounded-full border px-2 py-0.5 text-[11px] font-medium ${sentimentBadgeClasses(
                      r.label
                    )}`}
                  >
                    {r.label}
                  </span>
                </span>
                <span className="col-span-2 text-right font-mono text-ink-soft">
                  {formatPercent(r.confidence)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
