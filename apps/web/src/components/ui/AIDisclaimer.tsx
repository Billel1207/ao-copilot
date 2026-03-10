"use client";

import { Scale } from "lucide-react";
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
 * Legal disclaimer for AI-generated analysis.
 * Must appear at the bottom of every analysis tab.
 *
 * Default text: "Aide à la décision — ne se substitue pas à un conseil juridique"
 */
export default function AIDisclaimer({
  text = "Aide à la décision générée par intelligence artificielle — ne se substitue pas à un conseil juridique ou technique professionnel. Vérifiez toujours les résultats avec les documents originaux.",
  className,
  compact = false,
}: AIDisclaimerProps) {
  if (compact) {
    return (
      <p className={cn("text-[11px] text-slate-400 text-center pb-2", className)}>
        {text}
      </p>
    );
  }

  return (
    <div
      className={cn(
        "flex items-start gap-2.5 bg-slate-50 border border-slate-200 rounded-xl px-4 py-3",
        className
      )}
    >
      <Scale className="w-4 h-4 text-slate-400 flex-shrink-0 mt-0.5" />
      <div>
        <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide mb-0.5">
          Avertissement
        </p>
        <p className="text-xs text-slate-500 leading-relaxed">
          {text}
        </p>
      </div>
    </div>
  );
}
