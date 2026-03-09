"use client";
import { useGoNoGo } from "@/hooks/useAnalysis";
import { cn } from "@/lib/utils";
import { TrendingUp, TrendingDown, Minus, ShieldCheck, ShieldAlert, ShieldX, Loader2 } from "lucide-react";

interface Props {
  projectId: string;
}

// ── Couleurs selon score ────────────────────────────────────────────────────
function getScoreConfig(score: number, recommendation: string) {
  const reco = recommendation?.toUpperCase() ?? "";
  if (reco === "GO" || reco.startsWith("GO") && !reco.includes("NO") || score >= 70) {
    return {
      color:      "#059669",  // success-600
      bg:         "bg-emerald-50",
      border:     "border-emerald-200",
      textColor:  "text-emerald-700",
      label:      "GO",
      icon:       <ShieldCheck className="w-5 h-5" />,
      stroke:     "#059669",
      lightBg:    "bg-emerald-50",
    };
  }
  if (reco === "NO-GO" || reco.includes("NO") || score < 40) {
    return {
      color:      "#DC2626",
      bg:         "bg-red-50",
      border:     "border-red-200",
      textColor:  "text-red-700",
      label:      "NO-GO",
      icon:       <ShieldX className="w-5 h-5" />,
      stroke:     "#DC2626",
      lightBg:    "bg-red-50",
    };
  }
  return {
    color:      "#D97706",
    bg:         "bg-amber-50",
    border:     "border-amber-200",
    textColor:  "text-amber-700",
    label:      "ATTENTION",
    icon:       <ShieldAlert className="w-5 h-5" />,
    stroke:     "#D97706",
    lightBg:    "bg-amber-50",
  };
}

// ── Cercle SVG animé ────────────────────────────────────────────────────────
function ScoreCircle({ score, color }: { score: number; color: string }) {
  const r = 54;
  const circ = 2 * Math.PI * r;
  const dash = (score / 100) * circ;

  return (
    <svg width="140" height="140" viewBox="0 0 140 140" className="block">
      {/* Background circle */}
      <circle cx="70" cy="70" r={r} fill="none" stroke="#e2e8f0" strokeWidth="10" />
      {/* Progress arc */}
      <circle
        cx="70"
        cy="70"
        r={r}
        fill="none"
        stroke={color}
        strokeWidth="10"
        strokeLinecap="round"
        strokeDasharray={`${dash} ${circ}`}
        strokeDashoffset="0"
        transform="rotate(-90 70 70)"
        style={{ transition: "stroke-dasharray 1s ease-in-out" }}
      />
      {/* Score text */}
      <text
        x="70"
        y="67"
        textAnchor="middle"
        fontSize="28"
        fontWeight="800"
        fill={color}
        fontFamily="inherit"
      >
        {score}
      </text>
      <text
        x="70"
        y="84"
        textAnchor="middle"
        fontSize="11"
        fill="#94a3b8"
        fontFamily="inherit"
      >
        / 100
      </text>
    </svg>
  );
}

// ── Barre de dimension ──────────────────────────────────────────────────────
function DimensionBar({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: string;
}) {
  const pct = Math.max(0, Math.min(100, value));
  const barColor =
    pct >= 70 ? "#059669" : pct >= 40 ? "#D97706" : "#DC2626";

  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-slate-600 font-medium">{label}</span>
        <span className="font-bold" style={{ color: barColor }}>{pct}</span>
      </div>
      <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, backgroundColor: barColor }}
        />
      </div>
    </div>
  );
}

// ── Main Component ──────────────────────────────────────────────────────────
export function GoNoGoCard({ projectId }: Props) {
  const { data, isLoading, error } = useGoNoGo(projectId, true);

  if (isLoading) {
    return (
      <div className="card p-6 flex items-center justify-center gap-2 text-slate-400 animate-pulse">
        <Loader2 className="w-4 h-4 animate-spin" />
        <span className="text-sm">Chargement du score Go/No-Go…</span>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="card p-5 border-l-4 border-l-slate-200">
        <p className="text-sm text-slate-400">
          Score Go/No-Go non disponible — lancez l&apos;analyse pour obtenir une recommandation.
        </p>
      </div>
    );
  }

  const { score, recommendation, strengths = [], risks = [], summary, breakdown } = data;
  const cfg = getScoreConfig(score, recommendation);

  return (
    <div className={cn("card border-l-4 overflow-hidden animate-fade-in", cfg.border)}
      style={{ borderLeftColor: cfg.color }}>

      <div className="p-5 md:p-6">
        {/* Header row */}
        <div className="flex items-start gap-6 flex-wrap">

          {/* Score cercle */}
          <div className="flex flex-col items-center gap-2 flex-shrink-0">
            <ScoreCircle score={score} color={cfg.color} />
            <span className={cn(
              "inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-bold",
              cfg.bg, cfg.textColor
            )}>
              {cfg.icon}
              {cfg.label}
            </span>
          </div>

          {/* Synthèse + dimensions */}
          <div className="flex-1 min-w-0 space-y-4">
            {summary && (
              <p className="text-sm text-slate-700 leading-relaxed">{summary}</p>
            )}

            {breakdown && (
              <div className="space-y-2.5">
                <DimensionBar label="Adéquation technique"   value={breakdown.technical_fit}       color={cfg.color} />
                <DimensionBar label="Capacité financière"    value={breakdown.financial_capacity}   color={cfg.color} />
                <DimensionBar label="Faisabilité délais"     value={breakdown.timeline_feasibility} color={cfg.color} />
                <DimensionBar label="Position concurrentielle" value={breakdown.competitive_position} color={cfg.color} />
              </div>
            )}
          </div>
        </div>

        {/* Strengths & risks */}
        {(strengths.length > 0 || risks.length > 0) && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-5 pt-5 border-t border-slate-100">

            {/* Points forts */}
            {strengths.length > 0 && (
              <div>
                <div className="flex items-center gap-1.5 mb-2">
                  <TrendingUp className="w-3.5 h-3.5 text-emerald-600" />
                  <p className="text-xs font-semibold text-slate-600 uppercase tracking-wide">Points forts</p>
                </div>
                <ul className="space-y-1.5">
                  {strengths.slice(0, 3).map((s: string, i: number) => (
                    <li key={i} className="flex items-start gap-1.5 text-xs text-slate-700">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-1 flex-shrink-0" />
                      {s}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Risques */}
            {risks.length > 0 && (
              <div>
                <div className="flex items-center gap-1.5 mb-2">
                  <TrendingDown className="w-3.5 h-3.5 text-red-500" />
                  <p className="text-xs font-semibold text-slate-600 uppercase tracking-wide">Risques</p>
                </div>
                <ul className="space-y-1.5">
                  {risks.slice(0, 3).map((r: string, i: number) => (
                    <li key={i} className="flex items-start gap-1.5 text-xs text-slate-700">
                      <span className="w-1.5 h-1.5 rounded-full bg-red-400 mt-1 flex-shrink-0" />
                      {r}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
