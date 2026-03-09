import { cn } from "@/lib/utils";

interface Props {
  confidence: number | null;
  showLabel?: boolean;
}

export function ConfidenceBar({ confidence, showLabel = true }: Props) {
  if (confidence === null || confidence === undefined) return null;
  const pct = Math.round(confidence * 100);
  const color = pct >= 80 ? "bg-green-500" : pct >= 60 ? "bg-amber-400" : "bg-red-400";

  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
        <div className={cn("h-full rounded-full transition-all", color)} style={{ width: `${pct}%` }} />
      </div>
      {showLabel && <span className="text-xs text-slate-400 w-8 text-right">{pct}%</span>}
    </div>
  );
}
