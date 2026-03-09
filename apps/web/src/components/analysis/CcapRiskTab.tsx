"use client";

import { AlertTriangle, AlertOctagon, Info, ShieldAlert, FileX, CheckCircle } from "lucide-react";
import { useCcapRisks } from "@/hooks/useAnalysis";
import { cn } from "@/lib/utils";

interface Props {
  projectId: string;
}

// ── Types ──────────────────────────────────────────────────────────────────

type RiskLevel = "CRITIQUE" | "HAUT" | "MOYEN" | "BAS";

interface CcapClause {
  article_reference: string;
  clause_text: string;
  risk_level: RiskLevel;
  risk_type: string;
  conseil: string;
  citation: string;
}

interface CcapRisksData {
  clauses_risquees: CcapClause[];
  score_risque_global: number;
  nb_clauses_critiques: number;
  resume_risques: string;
  no_ccap_document?: boolean;
  no_ccap_text?: boolean;
  message?: string;
  ccap_docs_analyzed?: string[];
  model_used?: string;
}

// ── Risk level helpers ──────────────────────────────────────────────────────

const RISK_CONFIG: Record<RiskLevel, {
  label: string;
  badgeCls: string;
  cardBorderCls: string;
  cardBgCls: string;
  conseilBgCls: string;
  conseilTextCls: string;
  icon: React.ReactNode;
}> = {
  CRITIQUE: {
    label: "Critique",
    badgeCls: "bg-red-100 text-red-800 border border-red-200",
    cardBorderCls: "border-l-red-500",
    cardBgCls: "bg-white",
    conseilBgCls: "bg-red-50 border border-red-100",
    conseilTextCls: "text-red-900",
    icon: <AlertOctagon className="w-4 h-4 text-red-600" />,
  },
  HAUT: {
    label: "Haut",
    badgeCls: "bg-orange-100 text-orange-800 border border-orange-200",
    cardBorderCls: "border-l-orange-400",
    cardBgCls: "bg-white",
    conseilBgCls: "bg-orange-50 border border-orange-100",
    conseilTextCls: "text-orange-900",
    icon: <AlertTriangle className="w-4 h-4 text-orange-500" />,
  },
  MOYEN: {
    label: "Moyen",
    badgeCls: "bg-amber-100 text-amber-800 border border-amber-200",
    cardBorderCls: "border-l-amber-400",
    cardBgCls: "bg-white",
    conseilBgCls: "bg-amber-50 border border-amber-100",
    conseilTextCls: "text-amber-900",
    icon: <ShieldAlert className="w-4 h-4 text-amber-500" />,
  },
  BAS: {
    label: "Bas",
    badgeCls: "bg-green-100 text-green-800 border border-green-200",
    cardBorderCls: "border-l-green-400",
    cardBgCls: "bg-white",
    conseilBgCls: "bg-green-50 border border-green-100",
    conseilTextCls: "text-green-900",
    icon: <Info className="w-4 h-4 text-green-600" />,
  },
};

// ── Score circle ────────────────────────────────────────────────────────────

function ScoreCircle({ score }: { score: number }) {
  const size = 80;
  const strokeWidth = 7;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = Math.max(0, Math.min(100, score));
  const offset = circumference - (progress / 100) * circumference;

  const scoreColor =
    progress <= 30 ? "#059669"   // vert
    : progress <= 70 ? "#D97706" // amber
    : "#DC2626";                 // rouge

  const scoreLabel =
    progress <= 30 ? "Faible"
    : progress <= 70 ? "Modéré"
    : "Élevé";

  return (
    <div className="flex flex-col items-center gap-1">
      <div className="relative" style={{ width: size, height: size }}>
        {/* Track */}
        <svg width={size} height={size} className="rotate-[-90deg]">
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="#e2e8f0"
            strokeWidth={strokeWidth}
          />
          {/* Progress */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={scoreColor}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            style={{ transition: "stroke-dashoffset 0.6s ease" }}
          />
        </svg>
        {/* Score text */}
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-xl font-bold" style={{ color: scoreColor }}>
            {score}
          </span>
        </div>
      </div>
      <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
        {scoreLabel}
      </span>
    </div>
  );
}

// ── Risk badge ──────────────────────────────────────────────────────────────

function RiskBadge({ level }: { level: RiskLevel }) {
  const cfg = RISK_CONFIG[level] ?? RISK_CONFIG.MOYEN;
  return (
    <span className={cn("inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold", cfg.badgeCls)}>
      {cfg.icon}
      {cfg.label}
    </span>
  );
}

// ── Clause card ─────────────────────────────────────────────────────────────

function ClauseCard({ clause, index }: { clause: CcapClause; index: number }) {
  const cfg = RISK_CONFIG[clause.risk_level] ?? RISK_CONFIG.MOYEN;

  return (
    <div className={cn(
      "card border-l-4 p-4 space-y-2 animate-fade-in",
      cfg.cardBorderCls,
      cfg.cardBgCls,
    )}>
      {/* Header row */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-xs text-slate-400 font-mono w-5 shrink-0">{index + 1}</span>
          <div className="min-w-0">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide truncate">
              {clause.article_reference || "Article non précisé"}
            </p>
            <p className="text-sm font-medium text-slate-800 leading-snug mt-0.5">
              {clause.risk_type}
            </p>
          </div>
        </div>
        <div className="shrink-0">
          <RiskBadge level={clause.risk_level} />
        </div>
      </div>

      {/* Clause excerpt */}
      {clause.citation && (
        <blockquote className="text-xs text-slate-500 italic leading-relaxed bg-slate-50 rounded-lg px-3 py-2 border-l-2 border-slate-200">
          &ldquo;{clause.citation}&rdquo;
        </blockquote>
      )}

      {/* Conseil IA */}
      {clause.conseil && (
        <div className={cn("rounded-lg px-3 py-2", cfg.conseilBgCls)}>
          <p className="text-xs font-semibold mb-0.5" style={{ color: "inherit" }}>
            <span className="inline-flex items-center gap-1">
              {cfg.icon}
              <span className={cn("font-semibold text-xs", cfg.conseilTextCls)}>Conseil</span>
            </span>
          </p>
          <p className={cn("text-xs leading-relaxed", cfg.conseilTextCls)}>
            {clause.conseil}
          </p>
        </div>
      )}
    </div>
  );
}

// ── Level counter badge ─────────────────────────────────────────────────────

function LevelCounter({
  level,
  count,
}: {
  level: RiskLevel;
  count: number;
}) {
  const cfg = RISK_CONFIG[level];
  return (
    <div className="flex items-center gap-2">
      <span className={cn("inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold", cfg.badgeCls)}>
        {cfg.icon}
        {cfg.label}
      </span>
      <span className="text-sm font-bold text-slate-700">{count}</span>
    </div>
  );
}

// ── Skeleton loading ────────────────────────────────────────────────────────

function CcapSkeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      {/* Header skeleton */}
      <div className="card p-5 flex items-center gap-6">
        <div className="w-20 h-20 rounded-full bg-slate-200" />
        <div className="space-y-2 flex-1">
          <div className="h-4 bg-slate-200 rounded w-1/3" />
          <div className="h-3 bg-slate-100 rounded w-1/2" />
          <div className="flex gap-2 mt-2">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-6 w-16 bg-slate-100 rounded-full" />
            ))}
          </div>
        </div>
      </div>
      {/* Cards skeleton */}
      {[1, 2, 3].map((i) => (
        <div key={i} className="card border-l-4 border-l-slate-200 p-4 space-y-2">
          <div className="h-4 bg-slate-200 rounded w-2/3" />
          <div className="h-3 bg-slate-100 rounded w-full" />
          <div className="h-3 bg-slate-100 rounded w-3/4" />
        </div>
      ))}
    </div>
  );
}

// ── Main component ──────────────────────────────────────────────────────────

export function CcapRiskTab({ projectId }: Props) {
  const { data, isLoading, isError } = useCcapRisks(projectId);

  if (isLoading) return <CcapSkeleton />;

  if (isError) {
    return (
      <div className="card p-8 flex flex-col items-center gap-3 text-center animate-fade-in">
        <AlertTriangle className="w-10 h-10 text-amber-400" />
        <p className="text-slate-600 font-medium">Impossible de charger l&apos;analyse des risques CCAP.</p>
        <p className="text-slate-400 text-sm">Vérifiez que l&apos;analyse du projet a bien été lancée.</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="card p-8 flex flex-col items-center gap-3 text-center animate-fade-in">
        <FileX className="w-10 h-10 text-slate-300" />
        <p className="text-slate-500">Aucune donnée disponible.</p>
      </div>
    );
  }

  const ccapData = data as CcapRisksData;

  // Empty state : pas de document CCAP ou pas de texte
  if (ccapData.no_ccap_document || ccapData.no_ccap_text) {
    return (
      <div className="card p-10 flex flex-col items-center gap-4 text-center animate-fade-in">
        <div className="w-14 h-14 rounded-2xl bg-slate-100 flex items-center justify-center">
          <FileX className="w-7 h-7 text-slate-400" />
        </div>
        <div className="space-y-1">
          <p className="font-semibold text-slate-700">Aucun document CCAP disponible</p>
          <p className="text-slate-400 text-sm max-w-sm">
            {ccapData.message ?? "Uploadez un CCAP pour activer l'analyse automatique des clauses risquées."}
          </p>
        </div>
      </div>
    );
  }

  // Empty state : CCAP analysé mais pas de risques
  if (ccapData.clauses_risquees.length === 0) {
    return (
      <div className="space-y-4 animate-fade-in">
        <div className="card p-6 flex items-center gap-5">
          <ScoreCircle score={0} />
          <div>
            <p className="font-semibold text-slate-800">Analyse des risques CCAP</p>
            <p className="text-slate-400 text-sm mt-0.5">
              {ccapData.ccap_docs_analyzed?.join(", ") ?? "Document analysé"}
            </p>
          </div>
        </div>
        <div className="card p-10 flex flex-col items-center gap-4 text-center">
          <CheckCircle className="w-12 h-12 text-green-500" />
          <div className="space-y-1">
            <p className="font-semibold text-slate-700">Aucune clause risquée détectée</p>
            <p className="text-slate-400 text-sm max-w-sm">
              Le CCAP analysé ne présente pas de clauses problématiques selon les critères BTP français.
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Compteurs par niveau
  const clauses = ccapData.clauses_risquees;
  const countByLevel = (level: RiskLevel) =>
    clauses.filter((c) => c.risk_level === level).length;

  // Trier : CRITIQUE → HAUT → MOYEN → BAS
  const ORDER: RiskLevel[] = ["CRITIQUE", "HAUT", "MOYEN", "BAS"];
  const sortedClauses = [...clauses].sort(
    (a, b) => ORDER.indexOf(a.risk_level) - ORDER.indexOf(b.risk_level)
  );

  return (
    <div className="space-y-4 animate-fade-in">
      {/* ── Header card ── */}
      <div className="card p-5">
        <div className="flex flex-col sm:flex-row sm:items-center gap-5">
          {/* Score circle */}
          <div className="shrink-0">
            <ScoreCircle score={ccapData.score_risque_global} />
          </div>

          {/* Info + counters */}
          <div className="flex-1 space-y-3">
            <div>
              <p className="font-semibold text-slate-800 text-base">
                Analyse des risques CCAP
              </p>
              {ccapData.ccap_docs_analyzed && ccapData.ccap_docs_analyzed.length > 0 && (
                <p className="text-xs text-slate-400 mt-0.5">
                  {ccapData.ccap_docs_analyzed.join(", ")}
                </p>
              )}
            </div>

            {/* Counters */}
            <div className="flex flex-wrap gap-x-5 gap-y-2">
              {(["CRITIQUE", "HAUT", "MOYEN", "BAS"] as RiskLevel[]).map((level) => (
                <LevelCounter key={level} level={level} count={countByLevel(level)} />
              ))}
            </div>
          </div>
        </div>

        {/* Resume */}
        {ccapData.resume_risques && (
          <div className="mt-4 pt-4 border-t border-slate-100">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">
              Synthese
            </p>
            <p className="text-sm text-slate-700 leading-relaxed">
              {ccapData.resume_risques}
            </p>
          </div>
        )}
      </div>

      {/* ── Clause cards ── */}
      <div className="space-y-3">
        {sortedClauses.map((clause, i) => (
          <ClauseCard key={i} clause={clause} index={i} />
        ))}
      </div>

      {/* ── Footer note ── */}
      <p className="text-[11px] text-slate-400 text-center pb-2">
        Analyse générée automatiquement par IA — vérifiez les clauses avec votre service juridique avant de signer.
      </p>
    </div>
  );
}
