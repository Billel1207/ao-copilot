"use client";

import { AlertTriangle, ShieldCheck, ShieldAlert } from "lucide-react";
import { cn } from "@/lib/utils";

interface ConfidenceWarningProps {
  /** Confidence score between 0.0 and 1.0 */
  confidence: number | null | undefined;
  /** Additional CSS classes */
  className?: string;
  /** Show even when confidence is high (displays a green banner) */
  showWhenHigh?: boolean;
}

/**
 * Banner displaying the AI confidence level for an analysis.
 *
 * - confidence < 0.5 → amber warning "Confiance faible — vérifiez manuellement"
 * - confidence 0.5-0.75 → blue info "Confiance modérée"
 * - confidence ≥ 0.75 → green (only shown if showWhenHigh=true)
 * - confidence null/undefined → hidden
 */
export default function ConfidenceWarning({
  confidence,
  className,
  showWhenHigh = false,
}: ConfidenceWarningProps) {
  if (confidence == null || confidence === undefined) return null;

  const pct = Math.round(confidence * 100);

  // High confidence
  if (confidence >= 0.75) {
    if (!showWhenHigh) return null;
    return (
      <div
        className={cn(
          "flex items-center gap-2.5 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-xl px-4 py-2.5",
          className
        )}
      >
        <ShieldCheck className="w-4 h-4 text-green-600 flex-shrink-0" />
        <p className="text-xs text-green-800 dark:text-green-300">
          <span className="font-semibold">Confiance {pct}%</span>
          {" — "}Analyse fiable, données cohérentes avec les documents sources.
        </p>
      </div>
    );
  }

  // Moderate confidence
  if (confidence >= 0.5) {
    return (
      <div
        className={cn(
          "flex items-center gap-2.5 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl px-4 py-2.5",
          className
        )}
      >
        <ShieldAlert className="w-4 h-4 text-blue-600 flex-shrink-0" />
        <p className="text-xs text-blue-800 dark:text-blue-300">
          <span className="font-semibold">Confiance modérée ({pct}%)</span>
          {" — "}Certains éléments peuvent nécessiter une vérification manuelle.
        </p>
      </div>
    );
  }

  // Low confidence
  return (
    <div
      className={cn(
        "flex items-center gap-2.5 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700 rounded-xl px-4 py-2.5",
        className
      )}
    >
      <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0" />
      <p className="text-xs text-amber-800 dark:text-amber-300">
        <span className="font-semibold">Confiance faible ({pct}%)</span>
        {" — "}Les résultats de cette analyse sont incertains. Vérifiez manuellement avec les documents originaux.
      </p>
    </div>
  );
}
