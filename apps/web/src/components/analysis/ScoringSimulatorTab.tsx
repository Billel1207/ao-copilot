"use client";

import {
  Target,
  TrendingUp,
  Award,
  AlertTriangle,
  Info,
  Lightbulb,
  BarChart3,
  Star,
} from "lucide-react";
import { useScoringSimulation } from "@/hooks/useAnalysis";
import { cn } from "@/lib/utils";
import { AnalysisTabWrapper } from "@/components/analysis/AnalysisTabWrapper";

interface Props {
  projectId: string;
}

// -- Types -------------------------------------------------------------------

interface ScoringDimension {
  criterion: string;
  weight_pct: number;
  estimated_score: number;
  max_score: number;
  justification: string;
  tips_to_improve: string[];
}

type ClassementProbable = "Top 3" | "Milieu de peloton" | "Risqué";

interface ScoringSimulationData {
  dimensions: ScoringDimension[];
  note_technique_estimee: number;
  note_financiere_estimee: number;
  note_globale_estimee: number;
  classement_probable: ClassementProbable;
  axes_amelioration: string[];
  resume: string;
  model_used: string;
  has_company_profile: boolean;
}

// -- Color helpers -----------------------------------------------------------

function noteColor(note: number): string {
  if (note > 14) return "#059669";  // green
  if (note >= 10) return "#D97706"; // amber
  return "#DC2626";                 // red
}

function ratioColor(ratio: number): {
  border: string;
  barBg: string;
  barFill: string;
  text: string;
} {
  if (ratio > 0.7) return {
    border: "border-l-green-500",
    barBg: "bg-green-100",
    barFill: "bg-green-500",
    text: "text-green-700",
  };
  if (ratio >= 0.5) return {
    border: "border-l-amber-400",
    barBg: "bg-amber-100",
    barFill: "bg-amber-500",
    text: "text-amber-700",
  };
  return {
    border: "border-l-red-500",
    barBg: "bg-red-100",
    barFill: "bg-red-500",
    text: "text-red-700",
  };
}

const CLASSEMENT_CONFIG: Record<ClassementProbable, {
  badgeCls: string;
  icon: React.ReactNode;
}> = {
  "Top 3": {
    badgeCls: "bg-green-100 text-green-800 border border-green-200",
    icon: <Award className="w-4 h-4 text-green-600" />,
  },
  "Milieu de peloton": {
    badgeCls: "bg-amber-100 text-amber-800 border border-amber-200",
    icon: <BarChart3 className="w-4 h-4 text-amber-600" />,
  },
  "Risqué": {
    badgeCls: "bg-red-100 text-red-800 border border-red-200",
    icon: <AlertTriangle className="w-4 h-4 text-red-600" />,
  },
};

// -- Score circle /20 --------------------------------------------------------

function ScoreCircle20({ score: rawScore, label }: { score: number; label?: string }) {
  const score = Number.isFinite(rawScore) ? rawScore : 0;
  const size = 96;
  const strokeWidth = 8;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = Math.max(0, Math.min(20, score));
  const offset = circumference - (progress / 20) * circumference;
  const color = noteColor(progress);

  return (
    <div className="flex flex-col items-center gap-1">
      <div
        className="relative"
        style={{ width: size, height: size }}
        role="meter"
        aria-valuenow={score}
        aria-valuemin={0}
        aria-valuemax={20}
        aria-label={`${label ?? "Score"} : ${score.toFixed(1)} sur 20`}
      >
        <svg width={size} height={size} className="rotate-[-90deg]" aria-hidden="true">
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="#e2e8f0"
            strokeWidth={strokeWidth}
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            style={{ transition: "stroke-dashoffset 0.6s ease" }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-bold" style={{ color }}>
            {score.toFixed(1)}
          </span>
          <span className="text-[10px] text-slate-400 dark:text-slate-500 font-medium">/20</span>
        </div>
      </div>
      {label && (
        <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
          {label}
        </span>
      )}
    </div>
  );
}

// -- Stat mini card ----------------------------------------------------------

function StatCard({
  label,
  value,
  color,
  icon,
}: {
  label: string;
  value: number;
  color: string;
  icon: React.ReactNode;
}) {
  return (
    <div className="card p-3 flex items-center gap-3">
      <div
        className="w-10 h-10 rounded-xl flex items-center justify-center"
        style={{ backgroundColor: `${color}15` }}
      >
        {icon}
      </div>
      <div>
        <p className="text-lg font-bold" style={{ color }}>
          {value.toFixed(1)}<span className="text-xs text-slate-400 dark:text-slate-500 font-medium ml-0.5">/20</span>
        </p>
        <p className="text-[11px] text-slate-500 dark:text-slate-400 font-medium">{label}</p>
      </div>
    </div>
  );
}

// -- Dimension card ----------------------------------------------------------

function DimensionCard({ dim, index }: { dim: ScoringDimension; index: number }) {
  const ratio = dim.max_score > 0 ? dim.estimated_score / dim.max_score : 0;
  const colors = ratioColor(ratio);
  const pctWidth = Math.min(100, ratio * 100);

  return (
    <div
      className={cn(
        "card border-l-4 p-4 space-y-3 animate-fade-in",
        colors.border,
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-xs text-slate-400 dark:text-slate-500 font-mono w-5 shrink-0">
            {index + 1}
          </span>
          <p className="text-sm font-semibold text-slate-800 dark:text-slate-100 leading-snug">
            {dim.criterion}
          </p>
        </div>
        <span className="shrink-0 inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-100 text-blue-800 border border-blue-200">
          {dim.weight_pct}%
        </span>
      </div>

      {/* Score bar */}
      <div className="space-y-1">
        <div className="flex items-center justify-between text-xs">
          <span className={cn("font-semibold", colors.text)}>
            {dim.estimated_score} / {dim.max_score}
          </span>
          <span className="text-slate-400 dark:text-slate-500">
            {(ratio * 100).toFixed(0)}%
          </span>
        </div>
        <div
          className={cn("h-2 rounded-full w-full", colors.barBg)}
          role="meter"
          aria-valuenow={dim.estimated_score}
          aria-valuemin={0}
          aria-valuemax={dim.max_score}
          aria-label={`${dim.criterion} : ${dim.estimated_score} sur ${dim.max_score}`}
        >
          <div
            className={cn("h-2 rounded-full transition-all duration-500", colors.barFill)}
            style={{ width: `${pctWidth}%` }}
          />
        </div>
      </div>

      {/* Justification */}
      {dim.justification && (
        <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          {dim.justification}
        </p>
      )}

      {/* Tips */}
      {dim.tips_to_improve.length > 0 && (
        <div className="rounded-lg px-3 py-2 bg-blue-50 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-800">
          <p className="text-xs font-semibold text-blue-800 dark:text-blue-300 mb-1 inline-flex items-center gap-1">
            <Lightbulb className="w-3.5 h-3.5" />
            Pistes d&apos;amélioration
          </p>
          <ul className="space-y-0.5">
            {dim.tips_to_improve.map((tip, i) => (
              <li key={i} className="text-xs text-blue-700 dark:text-blue-300 leading-relaxed flex items-start gap-1.5">
                <span className="text-blue-400 dark:text-blue-500 mt-0.5 shrink-0">&bull;</span>
                <span>{tip}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

// -- Skeleton ----------------------------------------------------------------

function ScoringSkeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      {/* Header skeleton */}
      <div className="card p-5 flex items-center gap-6">
        <div className="w-24 h-24 rounded-full bg-slate-200" />
        <div className="space-y-2 flex-1">
          <div className="h-4 bg-slate-200 rounded w-1/3" />
          <div className="h-3 bg-slate-100 rounded w-1/2" />
          <div className="flex gap-3 mt-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-14 w-28 bg-slate-100 rounded-lg" />
            ))}
          </div>
        </div>
      </div>
      {/* Dimension cards skeleton */}
      {[1, 2, 3].map((i) => (
        <div key={i} className="card border-l-4 border-l-slate-200 p-4 space-y-2">
          <div className="h-4 bg-slate-200 rounded w-2/3" />
          <div className="h-2 bg-slate-100 rounded w-full" />
          <div className="h-3 bg-slate-100 rounded w-3/4" />
        </div>
      ))}
    </div>
  );
}

// -- Main component ----------------------------------------------------------

export function ScoringSimulatorTab({ projectId }: Props) {
  const query = useScoringSimulation(projectId);

  return (
    <AnalysisTabWrapper<ScoringSimulationData>
      query={query as ReturnType<typeof useScoringSimulation>}
      errorMessage="Impossible de charger la simulation de notation."
      disclaimerText="Simulation indicative basée sur l'IA — les notes réelles dépendent de l'offre finale soumise. Ne se substitue pas à un conseil professionnel."
      skeleton={<ScoringSkeleton />}
    >
      {(data) => <ScoringContent data={data} />}
    </AnalysisTabWrapper>
  );
}

function ScoringContent({ data: scoring }: { data: ScoringSimulationData }) {
  // Empty dimensions
  if (!scoring.dimensions || scoring.dimensions.length === 0) {
    return (
      <div className="card p-10 flex flex-col items-center gap-4 text-center animate-fade-in">
        <div className="w-14 h-14 rounded-2xl bg-slate-100 dark:bg-slate-700 flex items-center justify-center">
          <Target className="w-7 h-7 text-slate-400 dark:text-slate-500" />
        </div>
        <div className="space-y-1">
          <p className="font-semibold text-slate-700 dark:text-slate-300">
            Aucune simulation disponible
          </p>
          <p className="text-slate-400 dark:text-slate-500 text-sm max-w-sm">
            Uploadez un RC ou CCTP pour activer la simulation de notation acheteur.
          </p>
        </div>
      </div>
    );
  }

  const classementCfg = CLASSEMENT_CONFIG[scoring.classement_probable] ?? CLASSEMENT_CONFIG["Risqué"];

  return (
    <div className="space-y-4 animate-fade-in">
      {/* -- Company profile banner -- */}
      {!scoring.has_company_profile && (
        <div className="card p-3 flex items-center gap-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-800">
          <Info className="w-5 h-5 text-blue-500 shrink-0" />
          <p className="text-xs text-blue-700 dark:text-blue-300 leading-relaxed">
            Configurez votre profil entreprise pour une simulation plus précise.
          </p>
        </div>
      )}

      {/* -- Header card -- */}
      <div className="card p-5">
        <div className="flex flex-col sm:flex-row sm:items-center gap-5">
          {/* Note globale circle */}
          <div className="shrink-0">
            <ScoreCircle20
              score={scoring.note_globale_estimee}
              label="Note globale"
            />
          </div>

          {/* Stat cards + classement */}
          <div className="flex-1 space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <StatCard
                label="Note technique"
                value={scoring.note_technique_estimee}
                color={noteColor(scoring.note_technique_estimee)}
                icon={<TrendingUp className="w-5 h-5" style={{ color: noteColor(scoring.note_technique_estimee) }} />}
              />
              <StatCard
                label="Note financière"
                value={scoring.note_financiere_estimee}
                color={noteColor(scoring.note_financiere_estimee)}
                icon={<Star className="w-5 h-5" style={{ color: noteColor(scoring.note_financiere_estimee) }} />}
              />
            </div>

            {/* Classement badge */}
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">
                Classement probable :
              </span>
              <span
                className={cn(
                  "inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold",
                  classementCfg.badgeCls,
                )}
                aria-label={`Classement probable : ${scoring.classement_probable}`}
              >
                {classementCfg.icon}
                {scoring.classement_probable}
              </span>
            </div>
          </div>
        </div>

        {/* Resume */}
        {scoring.resume && (
          <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-700">
            <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-1">
              Synthèse
            </p>
            <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
              {scoring.resume}
            </p>
          </div>
        )}
      </div>

      {/* -- Dimensions section -- */}
      <div>
        <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-3 px-1">
          Détail des critères ({scoring.dimensions.length})
        </p>
        <div className="space-y-3">
          {scoring.dimensions.map((dim, i) => (
            <DimensionCard key={i} dim={dim} index={i} />
          ))}
        </div>
      </div>

      {/* -- Axes d'amelioration -- */}
      {scoring.axes_amelioration && scoring.axes_amelioration.length > 0 && (
        <div className="card p-5 bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border border-blue-100 dark:border-blue-800">
          <p className="text-xs font-semibold text-blue-800 dark:text-blue-300 uppercase tracking-wide mb-3 inline-flex items-center gap-1.5">
            <Target className="w-4 h-4" />
            Axes d&apos;amélioration prioritaires
          </p>
          <ol className="space-y-2">
            {scoring.axes_amelioration.map((axe, i) => (
              <li
                key={i}
                className="flex items-start gap-2 text-sm text-slate-800 dark:text-slate-200 leading-relaxed"
              >
                <span className="shrink-0 w-5 h-5 rounded-full bg-blue-600 text-white text-xs font-bold flex items-center justify-center mt-0.5">
                  {i + 1}
                </span>
                <span>{axe}</span>
              </li>
            ))}
          </ol>
        </div>
      )}

    </div>
  );
}
