"use client";

import { type ReactNode } from "react";
import { type UseQueryResult } from "@tanstack/react-query";
import { AlertTriangle, FileX } from "lucide-react";
import AIDisclaimer from "@/components/ui/AIDisclaimer";

// ── Default shimmer skeleton ─────────────────────────────────────────────

function DefaultSkeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      <div className="card p-5 space-y-3">
        <div className="flex items-center gap-3">
          <div className="h-6 w-40 bg-slate-200 dark:bg-slate-700 rounded-full" />
          <div className="h-4 bg-slate-100 dark:bg-slate-700 rounded w-1/3" />
        </div>
        <div className="h-3 bg-slate-100 dark:bg-slate-700 rounded w-full" />
        <div className="h-3 bg-slate-100 dark:bg-slate-700 rounded w-3/4" />
      </div>
      {[1, 2, 3].map((i) => (
        <div key={i} className="card border-l-4 border-l-slate-200 dark:border-l-slate-600 p-4 space-y-2">
          <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-2/3" />
          <div className="h-3 bg-slate-100 dark:bg-slate-700 rounded w-full" />
          <div className="h-3 bg-slate-100 dark:bg-slate-700 rounded w-3/4" />
        </div>
      ))}
    </div>
  );
}

// ── Props ────────────────────────────────────────────────────────────────

interface AnalysisTabWrapperProps<T> {
  /** The React Query result from a useXxxAnalysis hook */
  query: UseQueryResult<T, unknown>;
  /** Error message shown when query fails */
  errorMessage?: string;
  /** Message shown when data is null/undefined */
  emptyMessage?: string;
  /** Custom disclaimer text (passed to AIDisclaimer) */
  disclaimerText?: string;
  /** Custom skeleton to show during loading. Falls back to DefaultSkeleton. */
  skeleton?: ReactNode;
  /** Render function called with the query data when available */
  children: (data: T) => ReactNode;
}

// ── Component ────────────────────────────────────────────────────────────

export function AnalysisTabWrapper<T>({
  query,
  errorMessage = "Impossible de charger cette analyse.",
  emptyMessage = "Aucune donnée disponible.",
  disclaimerText,
  skeleton,
  children,
}: AnalysisTabWrapperProps<T>) {
  // ── Loading ──
  if (query.isLoading) {
    return <>{skeleton ?? <DefaultSkeleton />}</>;
  }

  // ── Error ──
  if (query.isError) {
    return (
      <div className="card p-8 flex flex-col items-center gap-3 text-center animate-fade-in">
        <AlertTriangle className="w-10 h-10 text-amber-400" />
        <p className="text-slate-600 dark:text-slate-400 font-medium">
          {errorMessage}
        </p>
        <p className="text-slate-400 dark:text-slate-500 text-sm">
          Vérifiez que l&apos;analyse du projet a bien été lancée.
        </p>
      </div>
    );
  }

  // ── Empty / no data ──
  if (!query.data) {
    return (
      <div className="card p-8 flex flex-col items-center gap-3 text-center animate-fade-in">
        <FileX className="w-10 h-10 text-slate-300 dark:text-slate-600" />
        <p className="text-slate-500 dark:text-slate-400">{emptyMessage}</p>
      </div>
    );
  }

  // ── Data available ──
  return (
    <>
      {children(query.data as T)}
      <div className="mt-4">
        <AIDisclaimer text={disclaimerText} />
      </div>
    </>
  );
}

export default AnalysisTabWrapper;
