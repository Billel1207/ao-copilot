"use client";
import { useState } from "react";
import { FileText } from "lucide-react";
import { cn } from "@/lib/utils";

interface Citation {
  doc: string;
  page: number;
  quote: string;
}

interface Props {
  citations: Citation[];
}

export function CitationTooltip({ citations }: Props) {
  const [open, setOpen] = useState(false);

  if (!citations || citations.length === 0) return null;

  return (
    <div className="relative inline-block">
      <button
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
        onClick={() => setOpen(!open)}
        className="inline-flex items-center gap-1 text-xs text-primary-600 hover:text-primary-800 mt-1"
      >
        <FileText className="w-3 h-3" />
        {citations.length} source{citations.length > 1 ? "s" : ""}
      </button>

      {open && (
        <div className="absolute left-0 bottom-6 z-50 w-72 bg-white border border-slate-200 rounded-lg shadow-lg p-3 space-y-2">
          {citations.map((c, i) => (
            <div key={i} className="text-xs">
              <p className="font-medium text-slate-700">
                {c.doc} — page {c.page}
              </p>
              <p className="text-slate-500 italic mt-0.5 line-clamp-3">&ldquo;{c.quote}&rdquo;</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
