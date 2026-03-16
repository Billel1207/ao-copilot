"use client";

import { useState } from "react";
import {
  AlertTriangle,
  AlertOctagon,
  Info,
  ShieldAlert,
  FileX,
  CheckCircle,
  GitCompareArrows,
  FileText,
} from "lucide-react";
import { useConflicts } from "@/hooks/useAnalysis";
import { cn } from "@/lib/utils";
import AIDisclaimer from "@/components/ui/AIDisclaimer";
import ConfidenceWarning from "@/components/ui/ConfidenceWarning";

interface Props {
  projectId: string;
}

// ── Types ──────────────────────────────────────────────────────────────────

type Severite = "CRITIQUE" | "HAUT" | "MOYEN" | "BAS";

type Categorie =
  | "Délais"
  | "Montants"
  | "Exigences"
  | "Clauses illégales"
  | "Références"
  | "Dérogation CCAG"
  | "CCTP ↔ DPGF";

const CONFLICT_TYPE_LABELS: Record<string, Categorie> = {
  delai: "Délais",
  montant: "Montants",
  exigence: "Exigences",
  clause_illegale: "Clauses illégales",
  reference: "Références",
  deviation_ccag: "Dérogation CCAG",
  cctp_dpgf: "CCTP ↔ DPGF",
};

interface Conflit {
  description: string;
  document_1: string;
  document_2: string;
  article_1: string;
  article_2: string;
  severite: Severite;
  categorie: Categorie;
  recommandation: string;
}

interface ConflictsData {
  conflits?: Conflit[];
  conflicts?: ApiConflict[];
  nb_critiques: number;
  nb_total: number;
  resume: string;
  documents_analyzed: string[];
  model_used: string;
  no_conflicts_possible?: boolean;
  confidence_overall?: number;
  message?: string;
}

// API may return English keys — map to French interface
interface ApiConflict {
  conflict_type?: string;
  severity?: string;
  doc_a?: string;
  doc_b?: string;
  description: string;
  citation_a?: string;
  citation_b?: string;
  recommendation?: string;
}

function normalizeConflicts(data: ConflictsData): Conflit[] {
  // Already in French format
  if (data.conflits && data.conflits.length > 0) return data.conflits;
  // Map from English API format
  if (data.conflicts) {
    return data.conflicts.map((c) => ({
      description: c.description,
      document_1: c.doc_a ?? "",
      document_2: c.doc_b ?? "",
      article_1: c.citation_a ?? "",
      article_2: c.citation_b ?? "",
      severite: (c.severity?.toUpperCase() as Severite) ?? "MOYEN",
      categorie: CONFLICT_TYPE_LABELS[c.conflict_type ?? ""] ?? "Exigences",
      recommandation: c.recommendation ?? "",
    }));
  }
  return [];
}

// ── Severity helpers ──────────────────────────────────────────────────────

const SEVERITY_CONFIG: Record<
  Severite,
  {
    label: string;
    badgeCls: string;
    cardBorderCls: string;
    tipBgCls: string;
    tipTextCls: string;
    icon: React.ReactNode;
  }
> = {
  CRITIQUE: {
    label: "Critique",
    badgeCls: "bg-red-100 text-red-800 border border-red-200",
    cardBorderCls: "border-l-red-500",
    tipBgCls: "bg-red-50 border border-red-100",
    tipTextCls: "text-red-900",
    icon: <AlertOctagon className="w-4 h-4 text-red-600" />,
  },
  HAUT: {
    label: "Haut",
    badgeCls: "bg-orange-100 text-orange-800 border border-orange-200",
    cardBorderCls: "border-l-orange-400",
    tipBgCls: "bg-orange-50 border border-orange-100",
    tipTextCls: "text-orange-900",
    icon: <AlertTriangle className="w-4 h-4 text-orange-500" />,
  },
  MOYEN: {
    label: "Moyen",
    badgeCls: "bg-amber-100 text-amber-800 border border-amber-200",
    cardBorderCls: "border-l-amber-400",
    tipBgCls: "bg-amber-50 border border-amber-100",
    tipTextCls: "text-amber-900",
    icon: <ShieldAlert className="w-4 h-4 text-amber-500" />,
  },
  BAS: {
    label: "Bas",
    badgeCls: "bg-green-100 text-green-800 border border-green-200",
    cardBorderCls: "border-l-green-400",
    tipBgCls: "bg-green-50 border border-green-100",
    tipTextCls: "text-green-900",
    icon: <Info className="w-4 h-4 text-green-600" />,
  },
};

const CATEGORY_COLORS: Record<Categorie, string> = {
  "Délais": "bg-blue-100 text-blue-800 border border-blue-200",
  "Montants": "bg-purple-100 text-purple-800 border border-purple-200",
  "Exigences": "bg-indigo-100 text-indigo-800 border border-indigo-200",
  "Clauses illégales": "bg-rose-100 text-rose-800 border border-rose-200",
  "Références": "bg-slate-100 text-slate-700 border border-slate-200",
  "Dérogation CCAG": "bg-amber-100 text-amber-800 border border-amber-200",
  "CCTP ↔ DPGF": "bg-teal-100 text-teal-800 border border-teal-200",
};

// ── Severity badge ────────────────────────────────────────────────────────

function SeverityBadge({ level }: { level: Severite }) {
  const cfg = SEVERITY_CONFIG[level] ?? SEVERITY_CONFIG.MOYEN;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold",
        cfg.badgeCls
      )}
      aria-label={`Niveau de severite : ${cfg.label}`}
    >
      {cfg.icon}
      {cfg.label}
    </span>
  );
}

// ── Category badge ────────────────────────────────────────────────────────

function CategoryBadge({ categorie }: { categorie: Categorie }) {
  const cls = CATEGORY_COLORS[categorie] ?? CATEGORY_COLORS["Références"];
  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold",
        cls
      )}
      aria-label={`Categorie du conflit : ${categorie}`}
    >
      {categorie}
    </span>
  );
}

// ── Conflict card ─────────────────────────────────────────────────────────

function ConflictCard({ conflit, index }: { conflit: Conflit; index: number }) {
  const cfg = SEVERITY_CONFIG[conflit.severite] ?? SEVERITY_CONFIG.MOYEN;

  return (
    <div
      className={cn(
        "card border-l-4 p-4 space-y-3 animate-fade-in",
        cfg.cardBorderCls,
        "bg-white"
      )}
    >
      {/* Header row */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-xs text-slate-400 font-mono w-5 shrink-0">
            {index + 1}
          </span>
          <div className="flex flex-wrap items-center gap-2">
            <SeverityBadge level={conflit.severite} />
            <CategoryBadge categorie={conflit.categorie} />
          </div>
        </div>
      </div>

      {/* Documents comparison */}
      <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3">
        <div className="flex items-center gap-1.5 min-w-0">
          <FileText className="w-3.5 h-3.5 text-blue-500 shrink-0" />
          <span className="text-xs font-medium text-slate-700 truncate">
            {conflit.document_1}
          </span>
          {conflit.article_1 && (
            <span className="inline-flex items-center px-1.5 py-0.5 rounded bg-slate-100 text-[10px] font-mono text-slate-600 shrink-0">
              {conflit.article_1}
            </span>
          )}
        </div>
        <div className="hidden sm:block shrink-0">
          <GitCompareArrows className="w-4 h-4 text-slate-400" />
        </div>
        <span className="sm:hidden text-xs text-slate-400 font-medium pl-5">
          vs.
        </span>
        <div className="flex items-center gap-1.5 min-w-0">
          <FileText className="w-3.5 h-3.5 text-blue-500 shrink-0" />
          <span className="text-xs font-medium text-slate-700 truncate">
            {conflit.document_2}
          </span>
          {conflit.article_2 && (
            <span className="inline-flex items-center px-1.5 py-0.5 rounded bg-slate-100 text-[10px] font-mono text-slate-600 shrink-0">
              {conflit.article_2}
            </span>
          )}
        </div>
      </div>

      {/* Description */}
      <p className="text-sm text-slate-700 leading-relaxed">
        {conflit.description}
      </p>

      {/* Recommandation */}
      {conflit.recommandation && (
        <div className={cn("rounded-lg px-3 py-2", cfg.tipBgCls)}>
          <p className="text-xs font-semibold mb-0.5" style={{ color: "inherit" }}>
            <span className="inline-flex items-center gap-1">
              {cfg.icon}
              <span className={cn("font-semibold text-xs", cfg.tipTextCls)}>
                Recommandation
              </span>
            </span>
          </p>
          <p className={cn("text-xs leading-relaxed", cfg.tipTextCls)}>
            {conflit.recommandation}
          </p>
        </div>
      )}
    </div>
  );
}

// ── Category filter pill ──────────────────────────────────────────────────

function CategoryFilterPill({
  label,
  count,
  active,
  onClick,
}: {
  label: string;
  count: number;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold transition-colors",
        active
          ? "bg-blue-600 text-white shadow-sm"
          : "bg-slate-100 text-slate-600 hover:bg-slate-200"
      )}
    >
      {label}
      <span
        className={cn(
          "inline-flex items-center justify-center w-5 h-5 rounded-full text-[10px] font-bold",
          active ? "bg-white/20 text-white" : "bg-slate-200 text-slate-500"
        )}
      >
        {count}
      </span>
    </button>
  );
}

// ── Skeleton loading ──────────────────────────────────────────────────────

function ConflictsSkeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      {/* Header skeleton */}
      <div className="card p-5 space-y-3">
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 bg-slate-200 rounded-lg" />
          <div className="space-y-2 flex-1">
            <div className="h-4 bg-slate-200 rounded w-1/3" />
            <div className="h-3 bg-slate-100 rounded w-1/2" />
          </div>
        </div>
        <div className="flex gap-2 mt-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-5 w-16 bg-slate-100 rounded-full" />
          ))}
        </div>
      </div>
      {/* Filter pills skeleton */}
      <div className="flex gap-2">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-7 w-20 bg-slate-100 rounded-full" />
        ))}
      </div>
      {/* Cards skeleton */}
      {[1, 2, 3].map((i) => (
        <div
          key={i}
          className="card border-l-4 border-l-slate-200 p-4 space-y-2"
        >
          <div className="h-4 bg-slate-200 rounded w-2/3" />
          <div className="h-3 bg-slate-100 rounded w-full" />
          <div className="h-3 bg-slate-100 rounded w-3/4" />
        </div>
      ))}
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────

export function ConflictsTab({ projectId }: Props) {
  const { data, isLoading, isError } = useConflicts(projectId);
  const [activeCategory, setActiveCategory] = useState<string | null>(null);

  if (isLoading) return <ConflictsSkeleton />;

  if (isError) {
    return (
      <div className="card p-8 flex flex-col items-center gap-3 text-center animate-fade-in">
        <AlertTriangle className="w-10 h-10 text-amber-400" />
        <p className="text-slate-600 font-medium">
          Impossible de charger la détection des conflits.
        </p>
        <p className="text-slate-400 text-sm">
          Vérifiez que l&apos;analyse du projet a bien été lancée.
        </p>
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

  const conflictsData = data as ConflictsData;

  // Empty state: no conflicts possible (missing docs, etc.)
  if (conflictsData.no_conflicts_possible) {
    return (
      <div className="card p-10 flex flex-col items-center gap-4 text-center animate-fade-in">
        <div className="w-14 h-14 rounded-2xl bg-slate-100 flex items-center justify-center">
          <FileX className="w-7 h-7 text-slate-400" />
        </div>
        <div className="space-y-1">
          <p className="font-semibold text-slate-700">
            Analyse des conflits non disponible
          </p>
          <p className="text-slate-400 text-sm max-w-sm">
            {conflictsData.message ??
              "Uploadez plusieurs documents du DCE pour détecter les contradictions entre pièces."}
          </p>
        </div>
      </div>
    );
  }

  // Empty state: no conflicts detected
  const normalizedConflits = normalizeConflicts(conflictsData);
  if (normalizedConflits.length === 0) {
    return (
      <div className="space-y-4 animate-fade-in">
        <div className="card p-6 flex items-center gap-5">
          <div className="w-12 h-12 rounded-xl bg-green-50 flex items-center justify-center shrink-0">
            <GitCompareArrows className="w-6 h-6 text-green-600" />
          </div>
          <div>
            <p className="font-semibold text-slate-800">
              Détection des conflits intra-DCE
            </p>
            <p className="text-xs text-slate-400 mt-0.5">
              {conflictsData.documents_analyzed?.join(", ") ?? "Documents analysés"}
            </p>
          </div>
        </div>
        <div className="card p-10 flex flex-col items-center gap-4 text-center">
          <CheckCircle className="w-12 h-12 text-green-500" />
          <div className="space-y-1">
            <p className="font-semibold text-slate-700">
              Aucun conflit détecté
            </p>
            <p className="text-slate-400 text-sm max-w-sm">
              Les documents du DCE analysés ne présentent pas de contradictions entre eux.
            </p>
          </div>
        </div>
        <AIDisclaimer compact />
      </div>
    );
  }

  const conflits = normalizedConflits;

  // Category counts
  const allCategories = Array.from(
    new Set(conflits.map((c) => c.categorie))
  ) as Categorie[];
  const countByCategory = (cat: Categorie) =>
    conflits.filter((c) => c.categorie === cat).length;

  // Filter
  const filteredConflits = activeCategory
    ? conflits.filter((c) => c.categorie === activeCategory)
    : conflits;

  // Sort by severity: CRITIQUE -> HAUT -> MOYEN -> BAS
  const ORDER: Severite[] = ["CRITIQUE", "HAUT", "MOYEN", "BAS"];
  const sortedConflits = [...filteredConflits].sort(
    (a, b) => ORDER.indexOf(a.severite) - ORDER.indexOf(b.severite)
  );

  return (
    <div className="space-y-4 animate-fade-in">
      {/* ── Header card ── */}
      <div className="card p-5">
        <div className="flex flex-col sm:flex-row sm:items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-blue-50 flex items-center justify-center shrink-0">
            <GitCompareArrows className="w-6 h-6 text-blue-600" />
          </div>
          <div className="flex-1 space-y-2">
            <div className="flex items-center gap-3">
              <p className="font-semibold text-slate-800 text-base">
                Détection des conflits intra-DCE
              </p>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-100 text-blue-800 border border-blue-200">
                {conflictsData.nb_total} conflit{conflictsData.nb_total > 1 ? "s" : ""}
              </span>
              {conflictsData.nb_critiques > 0 && (
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-red-100 text-red-800 border border-red-200">
                  <AlertOctagon className="w-3 h-3" />
                  {conflictsData.nb_critiques} critique{conflictsData.nb_critiques > 1 ? "s" : ""}
                </span>
              )}
            </div>
            {/* Documents analyzed pills */}
            {conflictsData.documents_analyzed && conflictsData.documents_analyzed.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {conflictsData.documents_analyzed.map((doc, i) => (
                  <span
                    key={i}
                    className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-slate-100 text-[10px] font-medium text-slate-500"
                  >
                    <FileText className="w-3 h-3" />
                    {doc}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Resume */}
        {conflictsData.resume && (
          <div className="mt-4 pt-4 border-t border-slate-100">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">
              Synthèse
            </p>
            <p className="text-sm text-slate-700 leading-relaxed">
              {conflictsData.resume}
            </p>
          </div>
        )}
      </div>

      {/* ── Category filter pills ── */}
      <div className="flex flex-wrap gap-2">
        <CategoryFilterPill
          label="Tous"
          count={conflits.length}
          active={activeCategory === null}
          onClick={() => setActiveCategory(null)}
        />
        {allCategories.map((cat) => (
          <CategoryFilterPill
            key={cat}
            label={cat}
            count={countByCategory(cat)}
            active={activeCategory === cat}
            onClick={() =>
              setActiveCategory(activeCategory === cat ? null : cat)
            }
          />
        ))}
      </div>

      {/* ── Conflict cards ── */}
      <div className="space-y-3">
        {sortedConflits.map((conflit, i) => (
          <ConflictCard key={i} conflit={conflit} index={i} />
        ))}
      </div>

      {/* ── Confidence + Disclaimer ── */}
      <ConfidenceWarning confidence={conflictsData.confidence_overall} />
      <AIDisclaimer />
    </div>
  );
}
