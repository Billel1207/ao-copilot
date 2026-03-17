"use client";

import {
  AlertTriangle,
  AlertOctagon,
  FileX,
  ShieldAlert,
  Info,
  Banknote,
  Clock,
  Percent,
  TrendingUp,
  Scale,
  Shield,
} from "lucide-react";
import { useAeAnalysis } from "@/hooks/useAnalysis";
import { cn } from "@/lib/utils";
import AIDisclaimer from "@/components/ui/AIDisclaimer";

interface Props {
  projectId: string;
}

// ── Types ──────────────────────────────────────────────────────────────────

type PenaliteEvaluation = "NORMAL" | "SÉVÈRE" | "TRÈS SÉVÈRE";
type ClauseSeverity = "CRITIQUE" | "HAUT" | "MOYEN" | "BAS";

interface Penalite {
  type: string;
  montant_ou_taux: string;
  reference: string;
  evaluation: PenaliteEvaluation;
}

interface Garantie {
  type: string;
  montant_pct: number;
  duree: string;
  reference: string;
}

interface RevisionPrix {
  applicable: boolean;
  indice: string;
  formule: string;
}

interface ClauseRisquee {
  clause: string;
  risque: string;
  conseil: string;
  severity: ClauseSeverity;
}

interface AeAnalysisData {
  type_prix: string;
  revision_prix: RevisionPrix | null;
  penalites: Penalite[];
  garanties: Garantie[];
  retenue_garantie_pct: number;
  delai_paiement_jours: number;
  avance_forfaitaire_pct: number | null;
  clauses_risquees: ClauseRisquee[];
  resume: string;
  score_risque: number;
  model_used?: string;
  no_ae_document?: boolean;
  message?: string;
}

// ── Evaluation config ─────────────────────────────────────────────────────

const EVAL_CONFIG: Record<PenaliteEvaluation, {
  label: string;
  badgeCls: string;
  icon: React.ReactNode;
}> = {
  NORMAL: {
    label: "Normal",
    badgeCls: "bg-green-100 text-green-800 border border-green-200",
    icon: <Info className="w-3.5 h-3.5 text-green-600" />,
  },
  "SÉVÈRE": {
    label: "S\u00e9v\u00e8re",
    badgeCls: "bg-orange-100 text-orange-800 border border-orange-200",
    icon: <AlertTriangle className="w-3.5 h-3.5 text-orange-500" />,
  },
  "TRÈS SÉVÈRE": {
    label: "Tr\u00e8s s\u00e9v\u00e8re",
    badgeCls: "bg-red-100 text-red-800 border border-red-200",
    icon: <AlertOctagon className="w-3.5 h-3.5 text-red-600" />,
  },
};

// ── Clause severity config ────────────────────────────────────────────────

const SEVERITY_CONFIG: Record<ClauseSeverity, {
  label: string;
  badgeCls: string;
  cardBorderCls: string;
  conseilBgCls: string;
  conseilTextCls: string;
  icon: React.ReactNode;
}> = {
  CRITIQUE: {
    label: "Critique",
    badgeCls: "bg-red-100 text-red-800 border border-red-200",
    cardBorderCls: "border-l-red-500",
    conseilBgCls: "bg-red-50 border border-red-100",
    conseilTextCls: "text-red-900",
    icon: <AlertOctagon className="w-4 h-4 text-red-600" />,
  },
  HAUT: {
    label: "Haut",
    badgeCls: "bg-orange-100 text-orange-800 border border-orange-200",
    cardBorderCls: "border-l-orange-400",
    conseilBgCls: "bg-orange-50 border border-orange-100",
    conseilTextCls: "text-orange-900",
    icon: <AlertTriangle className="w-4 h-4 text-orange-500" />,
  },
  MOYEN: {
    label: "Moyen",
    badgeCls: "bg-amber-100 text-amber-800 border border-amber-200",
    cardBorderCls: "border-l-amber-400",
    conseilBgCls: "bg-amber-50 border border-amber-100",
    conseilTextCls: "text-amber-900",
    icon: <ShieldAlert className="w-4 h-4 text-amber-500" />,
  },
  BAS: {
    label: "Bas",
    badgeCls: "bg-green-100 text-green-800 border border-green-200",
    cardBorderCls: "border-l-green-400",
    conseilBgCls: "bg-green-50 border border-green-100",
    conseilTextCls: "text-green-900",
    icon: <Info className="w-4 h-4 text-green-600" />,
  },
};

// ── Score circle (same pattern as CCAP) ───────────────────────────────────

function ScoreCircle({ score }: { score: number }) {
  const size = 80;
  const strokeWidth = 7;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = Math.max(0, Math.min(100, score));
  const offset = circumference - (progress / 100) * circumference;

  const scoreColor =
    progress <= 30 ? "#059669"
    : progress <= 70 ? "#D97706"
    : "#DC2626";

  const scoreLabel =
    progress <= 30 ? "Faible"
    : progress <= 70 ? "Mod\u00e9r\u00e9"
    : "\u00c9lev\u00e9";

  return (
    <div className="flex flex-col items-center gap-1">
      <div
        className="relative"
        style={{ width: size, height: size }}
        role="meter"
        aria-valuenow={score}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`Score de risque : ${score} sur 100 (${scoreLabel})`}
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
            stroke={scoreColor}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            style={{ transition: "stroke-dashoffset 0.6s ease" }}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-xl font-bold" style={{ color: scoreColor }}>
            {score}
          </span>
        </div>
      </div>
      <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
        {scoreLabel}
      </span>
    </div>
  );
}

// ── Key metric card ───────────────────────────────────────────────────────

function MetricCard({
  icon,
  label,
  value,
  sublabel,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  sublabel?: string;
}) {
  return (
    <div className="card p-4 flex items-center gap-3 bg-white dark:bg-slate-800">
      <div className="w-9 h-9 rounded-lg bg-blue-50 flex items-center justify-center shrink-0">
        {icon}
      </div>
      <div className="min-w-0">
        <p className="text-xs text-slate-500 dark:text-slate-400 font-medium truncate">{label}</p>
        <p className="text-sm font-bold text-slate-800 dark:text-slate-100">{value}</p>
        {sublabel && <p className="text-xs text-slate-400 dark:text-slate-500">{sublabel}</p>}
      </div>
    </div>
  );
}

// ── Clause card ───────────────────────────────────────────────────────────

function AeClauseCard({ clause, index }: { clause: ClauseRisquee; index: number }) {
  const cfg = SEVERITY_CONFIG[clause.severity] ?? SEVERITY_CONFIG.MOYEN;

  return (
    <div className={cn("card border-l-4 p-4 space-y-2 animate-fade-in", cfg.cardBorderCls, "bg-white dark:bg-slate-800")}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-xs text-slate-400 dark:text-slate-500 font-mono w-5 shrink-0">{index + 1}</span>
          <div className="min-w-0">
            <p className="text-sm font-medium text-slate-800 dark:text-slate-100 leading-snug">
              {clause.clause}
            </p>
          </div>
        </div>
        <div className="shrink-0">
          <span
            className={cn("inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold", cfg.badgeCls)}
            aria-label={`Niveau de risque : ${cfg.label}`}
          >
            {cfg.icon}
            {cfg.label}
          </span>
        </div>
      </div>

      {/* Risque */}
      {clause.risque && (
        <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed bg-slate-50 dark:bg-slate-800 rounded-lg px-3 py-2 border-l-2 border-slate-200 dark:border-slate-700">
          {clause.risque}
        </p>
      )}

      {/* Conseil */}
      {clause.conseil && (
        <div className={cn("rounded-lg px-3 py-2", cfg.conseilBgCls)}>
          <p className="text-xs font-semibold mb-0.5">
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

// ── Skeleton loading ──────────────────────────────────────────────────────

function AeSkeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      {/* Header skeleton */}
      <div className="card p-5 flex items-center gap-6">
        <div className="w-20 h-20 rounded-full bg-slate-200" />
        <div className="space-y-2 flex-1">
          <div className="h-4 bg-slate-200 rounded w-1/3" />
          <div className="h-3 bg-slate-100 rounded w-1/2" />
        </div>
      </div>
      {/* Metrics skeleton */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="card p-4 space-y-2">
            <div className="h-9 w-9 bg-slate-200 rounded-lg" />
            <div className="h-3 bg-slate-100 rounded w-2/3" />
            <div className="h-4 bg-slate-200 rounded w-1/2" />
          </div>
        ))}
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

// ── Main component ────────────────────────────────────────────────────────

export function AeAnalysisTab({ projectId }: Props) {
  const { data, isLoading, isError } = useAeAnalysis(projectId);

  if (isLoading) return <AeSkeleton />;

  if (isError) {
    return (
      <div className="card p-8 flex flex-col items-center gap-3 text-center animate-fade-in">
        <AlertTriangle className="w-10 h-10 text-amber-400" />
        <p className="text-slate-600 dark:text-slate-400 font-medium">Impossible de charger l&apos;analyse de l&apos;Acte d&apos;Engagement.</p>
        <p className="text-slate-400 dark:text-slate-500 text-sm">V&eacute;rifiez que l&apos;analyse du projet a bien &eacute;t&eacute; lanc&eacute;e.</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="card p-8 flex flex-col items-center gap-3 text-center animate-fade-in">
        <FileX className="w-10 h-10 text-slate-300" />
        <p className="text-slate-500 dark:text-slate-400">Aucune donn&eacute;e disponible.</p>
      </div>
    );
  }

  const aeData = data as AeAnalysisData;

  // Empty state: no AE document
  if (aeData.no_ae_document) {
    return (
      <div className="card p-10 flex flex-col items-center gap-4 text-center animate-fade-in">
        <div className="w-14 h-14 rounded-2xl bg-slate-100 dark:bg-slate-700 flex items-center justify-center">
          <FileX className="w-7 h-7 text-slate-400 dark:text-slate-500" />
        </div>
        <div className="space-y-1">
          <p className="font-semibold text-slate-700 dark:text-slate-300">Aucun Acte d&apos;Engagement disponible</p>
          <p className="text-slate-400 dark:text-slate-500 text-sm max-w-sm">
            {aeData.message ?? "Uploadez un AE pour activer l\u2019analyse automatique des conditions financi\u00e8res et clauses risqu\u00e9es."}
          </p>
        </div>
      </div>
    );
  }

  // Sort clauses by severity: CRITIQUE -> HAUT -> MOYEN -> BAS
  const SEVERITY_ORDER: ClauseSeverity[] = ["CRITIQUE", "HAUT", "MOYEN", "BAS"];
  const sortedClauses = [...(aeData.clauses_risquees ?? [])].sort(
    (a, b) => SEVERITY_ORDER.indexOf(a.severity) - SEVERITY_ORDER.indexOf(b.severity)
  );

  return (
    <div className="space-y-4 animate-fade-in">
      {/* ── Header card with score ── */}
      <div className="card p-5">
        <div className="flex flex-col sm:flex-row sm:items-center gap-5">
          <div className="shrink-0">
            <ScoreCircle score={aeData.score_risque} />
          </div>
          <div className="flex-1 space-y-1">
            <p className="font-semibold text-slate-800 dark:text-slate-100 text-base">
              Analyse de l&apos;Acte d&apos;Engagement
            </p>
            <p className="text-xs text-slate-400 dark:text-slate-500">
              Score de risque financier et contractuel
            </p>
          </div>
        </div>

        {/* Resume */}
        {aeData.resume && (
          <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-700">
            <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-1">
              Synth&egrave;se
            </p>
            <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
              {aeData.resume}
            </p>
          </div>
        )}
      </div>

      {/* ── Key financial metrics ── */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <MetricCard
          icon={<Banknote className="w-4 h-4 text-blue-600" />}
          label="Type de prix"
          value={aeData.type_prix || "Non pr\u00e9cis\u00e9"}
        />
        <MetricCard
          icon={<Clock className="w-4 h-4 text-blue-600" />}
          label="D\u00e9lai paiement"
          value={aeData.delai_paiement_jours ? `${aeData.delai_paiement_jours} jours` : "Non pr\u00e9cis\u00e9"}
        />
        <MetricCard
          icon={<Percent className="w-4 h-4 text-blue-600" />}
          label="Retenue garantie"
          value={aeData.retenue_garantie_pct !== null && aeData.retenue_garantie_pct !== undefined ? `${aeData.retenue_garantie_pct} %` : "Non pr\u00e9cis\u00e9"}
        />
        <MetricCard
          icon={<TrendingUp className="w-4 h-4 text-blue-600" />}
          label="Avance forfaitaire"
          value={aeData.avance_forfaitaire_pct !== null && aeData.avance_forfaitaire_pct !== undefined ? `${aeData.avance_forfaitaire_pct} %` : "Aucune"}
        />
      </div>

      {/* ── Penalites ── */}
      {aeData.penalites && aeData.penalites.length > 0 && (
        <div className="space-y-3">
          <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide px-1">
            P&eacute;nalit&eacute;s ({aeData.penalites.length})
          </p>
          {aeData.penalites.map((pen, i) => {
            const evalCfg = EVAL_CONFIG[pen.evaluation] ?? EVAL_CONFIG.NORMAL;
            const borderColor =
              pen.evaluation === "TRÈS SÉVÈRE" ? "border-l-red-500"
              : pen.evaluation === "SÉVÈRE" ? "border-l-orange-400"
              : "border-l-green-400";

            return (
              <div key={i} className={cn("card border-l-4 p-4 space-y-1 animate-fade-in bg-white dark:bg-slate-800", borderColor)}>
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-slate-800 dark:text-slate-100">{pen.type}</p>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{pen.montant_ou_taux}</p>
                  </div>
                  <div className="shrink-0">
                    <span
                      className={cn("inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold", evalCfg.badgeCls)}
                      aria-label={`Evaluation de la penalite : ${evalCfg.label}`}
                    >
                      {evalCfg.icon}
                      {evalCfg.label}
                    </span>
                  </div>
                </div>
                {pen.reference && (
                  <p className="text-xs text-slate-400 dark:text-slate-500">{pen.reference}</p>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* ── Garanties ── */}
      {aeData.garanties && aeData.garanties.length > 0 && (
        <div className="card p-4 space-y-3 dark:bg-slate-900">
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-blue-600" />
            <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">
              Garanties ({aeData.garanties.length})
            </p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100 dark:border-slate-700">
                  <th className="text-left py-2 px-3 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
                    Type
                  </th>
                  <th className="text-right py-2 px-3 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide w-24">
                    Montant
                  </th>
                  <th className="text-left py-2 px-3 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide w-32">
                    Dur&eacute;e
                  </th>
                  <th className="text-left py-2 px-3 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide w-32">
                    R&eacute;f&eacute;rence
                  </th>
                </tr>
              </thead>
              <tbody>
                {aeData.garanties.map((gar, i) => (
                  <tr key={i} className="border-b border-slate-50 dark:border-slate-700 last:border-b-0 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors">
                    <td className="py-2 px-3 text-slate-700 dark:text-slate-300">{gar.type}</td>
                    <td className="py-2 px-3 text-right text-slate-600 dark:text-slate-400 font-medium">
                      {gar.montant_pct !== null && gar.montant_pct !== undefined ? `${gar.montant_pct} %` : "\u2014"}
                    </td>
                    <td className="py-2 px-3 text-slate-600 dark:text-slate-400">{gar.duree || "\u2014"}</td>
                    <td className="py-2 px-3 text-slate-400 dark:text-slate-500 text-xs">{gar.reference || "\u2014"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── Clauses risquees ── */}
      {sortedClauses.length > 0 && (
        <div className="space-y-3">
          <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide px-1">
            Clauses risqu&eacute;es ({sortedClauses.length})
          </p>
          {sortedClauses.map((clause, i) => (
            <AeClauseCard key={i} clause={clause} index={i} />
          ))}
        </div>
      )}

      {/* ── Revision des prix ── */}
      {aeData.revision_prix && (
        <div className="card p-4 space-y-2 bg-white dark:bg-slate-900">
          <div className="flex items-center gap-2">
            <Scale className="w-4 h-4 text-blue-600" />
            <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">R&eacute;vision des prix</p>
          </div>
          <div className="space-y-2 text-sm text-slate-600 dark:text-slate-400">
            <div className="flex items-center gap-2">
              {aeData.revision_prix.applicable ? (
                <span
                  className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-green-100 text-green-800 border border-green-200"
                  aria-label="Revision des prix : Applicable"
                >
                  Applicable
                </span>
              ) : (
                <span
                  className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-red-100 text-red-800 border border-red-200"
                  aria-label="Revision des prix : Non applicable"
                >
                  Non applicable
                </span>
              )}
            </div>
            {aeData.revision_prix.indice && (
              <p>
                <span className="font-medium text-slate-700 dark:text-slate-300">Indice :</span> {aeData.revision_prix.indice}
              </p>
            )}
            {aeData.revision_prix.formule && (
              <p>
                <span className="font-medium text-slate-700 dark:text-slate-300">Formule :</span> {aeData.revision_prix.formule}
              </p>
            )}
          </div>
        </div>
      )}

      {/* ── Footer disclaimer ── */}
      <AIDisclaimer />
    </div>
  );
}
