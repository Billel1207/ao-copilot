import { cn } from "@/lib/utils";

interface Props {
  criticality: string | null;
  size?: "sm" | "default";
}

const CONFIG = {
  "Éliminatoire": "bg-red-100 text-red-700 border-red-200",
  "Important": "bg-amber-100 text-amber-700 border-amber-200",
  "Info": "bg-slate-100 text-slate-600 border-slate-200",
};

export function BadgeCriticality({ criticality, size = "default" }: Props) {
  if (!criticality) return <span className="text-slate-400 text-xs">—</span>;
  const cls = CONFIG[criticality as keyof typeof CONFIG] || CONFIG["Info"];
  return (
    <span className={cn(
      "inline-flex items-center rounded-full border font-medium",
      size === "sm" ? "px-2 py-0.5 text-xs" : "px-2.5 py-0.5 text-xs",
      cls
    )}>
      {criticality === "Éliminatoire" && <span className="mr-1">🔴</span>}
      {criticality === "Important" && <span className="mr-1">🟡</span>}
      {criticality}
    </span>
  );
}
