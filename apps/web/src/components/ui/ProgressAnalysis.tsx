import { CheckCircle, Loader2, Circle } from "lucide-react";
import { cn } from "@/lib/utils";

const STEPS = [
  { key: "upload", label: "Upload" },
  { key: "extract", label: "Extraction" },
  { key: "analyze", label: "Analyse IA" },
  { key: "ready", label: "Prêt" },
];

function stepIndex(status: string): number {
  if (status === "ready") return 4;
  if (status === "analyzing") return 2;
  if (status === "processing") return 1;
  return 0;
}

interface Props {
  status: string;
}

export function ProgressAnalysis({ status }: Props) {
  const current = stepIndex(status);

  return (
    <div className="flex items-center gap-2">
      {STEPS.map((step, i) => (
        <div key={step.key} className="flex items-center gap-2">
          <div className={cn(
            "flex items-center gap-1.5 text-xs font-medium",
            i < current ? "text-green-600" : i === current ? "text-blue-600" : "text-slate-400"
          )}>
            {i < current ? (
              <CheckCircle className="w-4 h-4" />
            ) : i === current ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Circle className="w-4 h-4" />
            )}
            {step.label}
          </div>
          {i < STEPS.length - 1 && <div className="w-6 h-px bg-slate-200" />}
        </div>
      ))}
    </div>
  );
}
