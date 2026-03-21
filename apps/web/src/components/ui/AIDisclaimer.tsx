"use client";

import { Scale, Sparkles } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";

interface AIDisclaimerProps {
  /** Override the default disclaimer text */
  text?: string;
  /** Additional CSS classes */
  className?: string;
  /** Compact mode — single line, no icon */
  compact?: boolean;
}

/**
 * Legal disclaimer for AI-generated analysis — AI Act Article 50 compliance.
 *
 * Displays a visible "Généré par IA" badge on every AI-generated content view,
 * as required by EU Regulation 2024/1689 (AI Act) Article 50 for transparency.
 * Links to the /ai-transparency page for full disclosure.
 */
export default function AIDisclaimer({
  text = "Aide à la décision générée par intelligence artificielle — ne se substitue pas à un conseil juridique ou technique professionnel. Vérifiez toujours les résultats avec les documents originaux.",
  className,
  compact = false,
}: AIDisclaimerProps) {
  if (compact) {
    return (
      <p className={cn("text-[11px] text-slate-400 dark:text-slate-500 text-center pb-2", className)}>
        <span className="inline-flex items-center gap-1 mr-1">
          <Sparkles className="w-3 h-3" aria-hidden="true" />
          <span className="font-semibold">Généré par IA</span> —
        </span>
        {text}
      </p>
    );
  }

  return (
    <div
      className={cn(
        "flex items-start gap-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3",
        className
      )}
    >
      <Scale className="w-4 h-4 text-slate-400 flex-shrink-0 mt-0.5" aria-hidden="true" />
      <div>
        {/* ── AI Act Article 50 — Visible AI generation badge ── */}
        <div className="flex items-center gap-2 mb-1">
          <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 rounded-full text-[10px] font-bold uppercase tracking-wider">
            <Sparkles className="w-3 h-3" aria-hidden="true" />
            Généré par IA
          </span>
          <Link
            href="/ai-transparency"
            className="text-[10px] text-blue-500 dark:text-blue-400 hover:underline"
          >
            En savoir plus
          </Link>
        </div>
        <p className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-0.5">
          Avertissement
        </p>
        <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
          {text}
        </p>
      </div>
    </div>
  );
}
