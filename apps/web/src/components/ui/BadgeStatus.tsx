import { cn } from "@/lib/utils";

interface Props {
  status: string;
}

const CONFIG = {
  "OK": "bg-green-100 text-green-700 border-green-200",
  "MANQUANT": "bg-red-100 text-red-700 border-red-200",
  "À CLARIFIER": "bg-amber-100 text-amber-700 border-amber-200",
};

export function BadgeStatus({ status }: Props) {
  const cls = CONFIG[status as keyof typeof CONFIG] || "bg-slate-100 text-slate-600 border-slate-200";
  return (
    <span className={cn(
      "inline-flex items-center rounded-full border font-medium px-2.5 py-0.5 text-xs",
      cls
    )}>
      {status}
    </span>
  );
}
