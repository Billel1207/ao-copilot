"use client";

import {
  AlertTriangle,
  FileX,
  Layers,
  Users,
  Scissors,
  Shuffle,
  ShieldCheck,
  ShieldAlert,
  Info,
  BookOpen,
} from "lucide-react";
import { useRcAnalysis } from "@/hooks/useAnalysis";
import { cn } from "@/lib/utils";

interface Props {
  projectId: string;
}

// ── Types ──────────────────────────────────────────────────────────────────

interface ConditionAcces {
  condition: string;
  type: "éliminatoire" | "recommandé";
  reference_article: string;
}

interface Groupement {
  autorise: boolean;
  forme: string;
  mandataire_solidaire: boolean;
  restrictions: string;
}

interface SousTraitance {
  autorisee: boolean;
  conditions: string;
  plafond_pct: number | null;
}

interface Variantes {
  autorisees: boolean;
  conditions: string;
}

interface Lot {
  numero: string | number;
  intitule: string;
  montant_estime: string | number | null;
}

interface RcAnalysisData {
  conditions_acces: ConditionAcces[];
  groupement: Groupement | null;
  sous_traitance: SousTraitance | null;
  variantes: Variantes | null;
  procedure_type: string;
  lots: Lot[];
  resume: string;
  alertes: string[];
  model_used?: string;
  no_rc_document?: boolean;
  message?: string;
}

// ── Condition type config ─────────────────────────────────────────────────

const CONDITION_CONFIG = {
  éliminatoire: {
    label: "Éliminatoire",
    badgeCls: "bg-red-100 text-red-800 border border-red-200",
    borderCls: "border-l-red-500",
    icon: <ShieldAlert className="w-4 h-4 text-red-600" />,
  },
  recommandé: {
    label: "Recommandé",
    badgeCls: "bg-amber-100 text-amber-800 border border-amber-200",
    borderCls: "border-l-amber-400",
    icon: <Info className="w-4 h-4 text-amber-500" />,
  },
} as const;

// ── Procedure badge ───────────────────────────────────────────────────────

function ProcedureBadge({ type }: { type: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-800 border border-blue-200">
      <BookOpen className="w-3.5 h-3.5" />
      {type}
    </span>
  );
}

// ── Condition card ────────────────────────────────────────────────────────

function ConditionCard({ condition, index }: { condition: ConditionAcces; index: number }) {
  const cfg = CONDITION_CONFIG[condition.type] ?? CONDITION_CONFIG.recommandé;

  return (
    <div className={cn("card border-l-4 p-4 space-y-1 animate-fade-in", cfg.borderCls, "bg-white")}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-xs text-slate-400 font-mono w-5 shrink-0">{index + 1}</span>
          <div className="min-w-0">
            {condition.reference_article && (
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide truncate">
                {condition.reference_article}
              </p>
            )}
            <p className="text-sm font-medium text-slate-800 leading-snug mt-0.5">
              {condition.condition}
            </p>
          </div>
        </div>
        <div className="shrink-0">
          <span className={cn("inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold", cfg.badgeCls)}>
            {cfg.icon}
            {cfg.label}
          </span>
        </div>
      </div>
    </div>
  );
}

// ── Info card ─────────────────────────────────────────────────────────────

function InfoCard({
  icon,
  title,
  children,
}: {
  icon: React.ReactNode;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="card p-4 space-y-2 bg-white">
      <div className="flex items-center gap-2">
        {icon}
        <p className="text-sm font-semibold text-slate-700">{title}</p>
      </div>
      <div className="text-sm text-slate-600 leading-relaxed">{children}</div>
    </div>
  );
}

// ── Skeleton loading ──────────────────────────────────────────────────────

function RcSkeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      {/* Header skeleton */}
      <div className="card p-5 space-y-3">
        <div className="flex items-center gap-3">
          <div className="h-6 w-40 bg-slate-200 rounded-full" />
          <div className="h-4 bg-slate-100 rounded w-1/3" />
        </div>
        <div className="h-3 bg-slate-100 rounded w-full" />
        <div className="h-3 bg-slate-100 rounded w-3/4" />
      </div>
      {/* Table skeleton */}
      <div className="card p-4 space-y-2">
        <div className="h-4 bg-slate-200 rounded w-1/4" />
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-8 bg-slate-100 rounded w-full" />
        ))}
      </div>
      {/* Cards skeleton */}
      {[1, 2, 3].map((i) => (
        <div key={i} className="card border-l-4 border-l-slate-200 p-4 space-y-2">
          <div className="h-4 bg-slate-200 rounded w-2/3" />
          <div className="h-3 bg-slate-100 rounded w-full" />
        </div>
      ))}
    </div>
  );
}

// ── Format montant ────────────────────────────────────────────────────────

function formatMontant(val: string | number | null): string {
  if (val === null || val === undefined || val === "") return "Non estimé";
  const num = typeof val === "string" ? parseFloat(val) : val;
  if (isNaN(num)) return String(val);
  return new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(num);
}

// ── Main component ────────────────────────────────────────────────────────

export function RcAnalysisTab({ projectId }: Props) {
  const { data, isLoading, isError } = useRcAnalysis(projectId);

  if (isLoading) return <RcSkeleton />;

  if (isError) {
    return (
      <div className="card p-8 flex flex-col items-center gap-3 text-center animate-fade-in">
        <AlertTriangle className="w-10 h-10 text-amber-400" />
        <p className="text-slate-600 font-medium">Impossible de charger l&apos;analyse du R&egrave;glement de Consultation.</p>
        <p className="text-slate-400 text-sm">V&eacute;rifiez que l&apos;analyse du projet a bien &eacute;t&eacute; lanc&eacute;e.</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="card p-8 flex flex-col items-center gap-3 text-center animate-fade-in">
        <FileX className="w-10 h-10 text-slate-300" />
        <p className="text-slate-500">Aucune donn&eacute;e disponible.</p>
      </div>
    );
  }

  const rcData = data as RcAnalysisData;

  // Empty state: no RC document
  if (rcData.no_rc_document) {
    return (
      <div className="card p-10 flex flex-col items-center gap-4 text-center animate-fade-in">
        <div className="w-14 h-14 rounded-2xl bg-slate-100 flex items-center justify-center">
          <FileX className="w-7 h-7 text-slate-400" />
        </div>
        <div className="space-y-1">
          <p className="font-semibold text-slate-700">Aucun R&egrave;glement de Consultation disponible</p>
          <p className="text-slate-400 text-sm max-w-sm">
            {rcData.message ?? "Uploadez un RC pour activer l\u2019analyse automatique des conditions de consultation."}
          </p>
        </div>
      </div>
    );
  }

  const conditionsEliminatoires = (rcData.conditions_acces ?? []).filter((c) => c.type === "éliminatoire");
  const conditionsRecommandees = (rcData.conditions_acces ?? []).filter((c) => c.type === "recommandé");
  const sortedConditions = [...conditionsEliminatoires, ...conditionsRecommandees];

  return (
    <div className="space-y-4 animate-fade-in">
      {/* ── Header card ── */}
      <div className="card p-5">
        <div className="flex flex-col sm:flex-row sm:items-center gap-4">
          <div className="flex-1 space-y-2">
            <div className="flex items-center gap-3 flex-wrap">
              <p className="font-semibold text-slate-800 text-base">
                Analyse du R&egrave;glement de Consultation
              </p>
              {rcData.procedure_type && <ProcedureBadge type={rcData.procedure_type} />}
            </div>
          </div>
        </div>

        {/* Resume */}
        {rcData.resume && (
          <div className="mt-4 pt-4 border-t border-slate-100">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">
              Synth&egrave;se
            </p>
            <p className="text-sm text-slate-700 leading-relaxed">
              {rcData.resume}
            </p>
          </div>
        )}
      </div>

      {/* ── Alertes ── */}
      {rcData.alertes && rcData.alertes.length > 0 && (
        <div className="card border-l-4 border-l-amber-400 bg-amber-50 p-4 space-y-2">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-600" />
            <p className="text-sm font-semibold text-amber-800">
              {rcData.alertes.length === 1 ? "Alerte" : "Alertes"}
            </p>
          </div>
          <ul className="space-y-1">
            {rcData.alertes.map((alerte, i) => (
              <li key={i} className="text-sm text-amber-700 leading-relaxed flex items-start gap-2">
                <span className="text-amber-400 mt-1 shrink-0">&bull;</span>
                <span>{alerte}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* ── Lots table ── */}
      {rcData.lots && rcData.lots.length > 0 && (
        <div className="card p-4 space-y-3">
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-blue-600" />
            <p className="text-sm font-semibold text-slate-700">
              Lots ({rcData.lots.length})
            </p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100">
                  <th className="text-left py-2 px-3 text-xs font-semibold text-slate-500 uppercase tracking-wide w-20">
                    N&deg;
                  </th>
                  <th className="text-left py-2 px-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                    Intitul&eacute;
                  </th>
                  <th className="text-right py-2 px-3 text-xs font-semibold text-slate-500 uppercase tracking-wide w-40">
                    Montant estim&eacute;
                  </th>
                </tr>
              </thead>
              <tbody>
                {rcData.lots.map((lot, i) => (
                  <tr key={i} className="border-b border-slate-50 last:border-b-0 hover:bg-slate-50 transition-colors">
                    <td className="py-2 px-3 text-slate-600 font-mono text-xs">
                      {lot.numero}
                    </td>
                    <td className="py-2 px-3 text-slate-700">
                      {lot.intitule}
                    </td>
                    <td className="py-2 px-3 text-right text-slate-600 font-medium">
                      {formatMontant(lot.montant_estime)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── Conditions d'acces ── */}
      {sortedConditions.length > 0 && (
        <div className="space-y-3">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide px-1">
            Conditions d&apos;acc&egrave;s ({sortedConditions.length})
          </p>
          {sortedConditions.map((cond, i) => (
            <ConditionCard key={i} condition={cond} index={i} />
          ))}
        </div>
      )}

      {/* ── Groupement ── */}
      {rcData.groupement && (
        <InfoCard
          icon={<Users className="w-4 h-4 text-blue-600" />}
          title="Groupement"
        >
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              {rcData.groupement.autorise ? (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-green-100 text-green-800 border border-green-200">
                  <ShieldCheck className="w-3.5 h-3.5" />
                  Autoris&eacute;
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-red-100 text-red-800 border border-red-200">
                  <ShieldAlert className="w-3.5 h-3.5" />
                  Non autoris&eacute;
                </span>
              )}
            </div>
            {rcData.groupement.forme && (
              <p className="text-sm text-slate-600">
                <span className="font-medium text-slate-700">Forme :</span> {rcData.groupement.forme}
              </p>
            )}
            {rcData.groupement.mandataire_solidaire && (
              <p className="text-xs text-amber-700 bg-amber-50 rounded px-2 py-1 border border-amber-100">
                Mandataire solidaire exig&eacute;
              </p>
            )}
            {rcData.groupement.restrictions && (
              <p className="text-sm text-slate-600">
                <span className="font-medium text-slate-700">Restrictions :</span> {rcData.groupement.restrictions}
              </p>
            )}
          </div>
        </InfoCard>
      )}

      {/* ── Sous-traitance ── */}
      {rcData.sous_traitance && (
        <InfoCard
          icon={<Scissors className="w-4 h-4 text-blue-600" />}
          title="Sous-traitance"
        >
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              {rcData.sous_traitance.autorisee ? (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-green-100 text-green-800 border border-green-200">
                  <ShieldCheck className="w-3.5 h-3.5" />
                  Autoris&eacute;e
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-red-100 text-red-800 border border-red-200">
                  <ShieldAlert className="w-3.5 h-3.5" />
                  Non autoris&eacute;e
                </span>
              )}
              {rcData.sous_traitance.plafond_pct !== null && rcData.sous_traitance.plafond_pct !== undefined && (
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-200">
                  Plafond : {rcData.sous_traitance.plafond_pct} %
                </span>
              )}
            </div>
            {rcData.sous_traitance.conditions && (
              <p className="text-sm text-slate-600">{rcData.sous_traitance.conditions}</p>
            )}
          </div>
        </InfoCard>
      )}

      {/* ── Variantes ── */}
      {rcData.variantes && (
        <InfoCard
          icon={<Shuffle className="w-4 h-4 text-blue-600" />}
          title="Variantes"
        >
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              {rcData.variantes.autorisees ? (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-green-100 text-green-800 border border-green-200">
                  <ShieldCheck className="w-3.5 h-3.5" />
                  Autoris&eacute;es
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-red-100 text-red-800 border border-red-200">
                  <ShieldAlert className="w-3.5 h-3.5" />
                  Non autoris&eacute;es
                </span>
              )}
            </div>
            {rcData.variantes.conditions && (
              <p className="text-sm text-slate-600">{rcData.variantes.conditions}</p>
            )}
          </div>
        </InfoCard>
      )}

      {/* ── Footer note ── */}
      <p className="text-[11px] text-slate-400 text-center pb-2">
        Analyse g&eacute;n&eacute;r&eacute;e automatiquement par IA — v&eacute;rifiez avec les documents originaux.
      </p>
    </div>
  );
}
