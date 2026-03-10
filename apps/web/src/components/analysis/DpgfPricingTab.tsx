"use client";

import {
  AlertTriangle,
  AlertOctagon,
  FileX,
  TrendingDown,
  TrendingUp,
  CheckCircle,
  HelpCircle,
  BarChart3,
  Info,
} from "lucide-react";
import { useDpgfPricing } from "@/hooks/useAnalysis";
import { cn } from "@/lib/utils";
import AIDisclaimer from "@/components/ui/AIDisclaimer";

interface Props {
  projectId: string;
}

// -- Types -------------------------------------------------------------------

type PricingStatus = "SOUS_EVALUE" | "NORMAL" | "SUR_EVALUE" | "INCONNU";

interface PricingLine {
  designation: string;
  prix_unitaire: number;
  status: PricingStatus;
  ratio_vs_moyen: number;
  message: string;
  reference_nom: string;
  reference_prix_bas: number;
  reference_prix_haut: number;
  reference_prix_moyen: number;
  reference_unite: string;
}

interface DpgfPricingData {
  pricing_analysis: PricingLine[];
  total_lines: number;
  alerts: PricingLine[];
  message?: string;
}

// -- Status config -----------------------------------------------------------

const STATUS_CONFIG: Record<PricingStatus, {
  label: string;
  badgeCls: string;
  rowCls: string;
  borderCls: string;
  icon: React.ReactNode;
}> = {
  SOUS_EVALUE: {
    label: "Sous-évalué",
    badgeCls: "bg-orange-100 text-orange-800 border border-orange-200",
    rowCls: "bg-orange-50/60",
    borderCls: "border-l-orange-400",
    icon: <TrendingDown className="w-4 h-4 text-orange-500" />,
  },
  SUR_EVALUE: {
    label: "Surévalué",
    badgeCls: "bg-red-100 text-red-800 border border-red-200",
    rowCls: "bg-red-50/60",
    borderCls: "border-l-red-500",
    icon: <TrendingUp className="w-4 h-4 text-red-600" />,
  },
  NORMAL: {
    label: "Normal",
    badgeCls: "bg-green-100 text-green-800 border border-green-200",
    rowCls: "bg-green-50/40",
    borderCls: "border-l-green-500",
    icon: <CheckCircle className="w-4 h-4 text-green-600" />,
  },
  INCONNU: {
    label: "Inconnu",
    badgeCls: "bg-slate-100 text-slate-600 border border-slate-200",
    rowCls: "bg-slate-50/40",
    borderCls: "border-l-slate-300",
    icon: <HelpCircle className="w-4 h-4 text-slate-400" />,
  },
};

// -- Status badge ------------------------------------------------------------

function StatusBadge({ status }: { status: PricingStatus }) {
  const cfg = STATUS_CONFIG[status] ?? STATUS_CONFIG.INCONNU;
  return (
    <span
      className={cn("inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold", cfg.badgeCls)}
      aria-label={`Statut tarifaire : ${cfg.label}`}
    >
      {cfg.icon}
      {cfg.label}
    </span>
  );
}

// -- Stat counter ------------------------------------------------------------

function StatCounter({
  label,
  count,
  badgeCls,
  icon,
}: {
  label: string;
  count: number;
  badgeCls: string;
  icon: React.ReactNode;
}) {
  return (
    <div className="flex items-center gap-2">
      <span className={cn("inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold", badgeCls)}>
        {icon}
        {label}
      </span>
      <span className="text-sm font-bold text-slate-700">{count}</span>
    </div>
  );
}

// -- Alert card --------------------------------------------------------------

function AlertCard({ line }: { line: PricingLine }) {
  const cfg = STATUS_CONFIG[line.status] ?? STATUS_CONFIG.INCONNU;

  return (
    <div className={cn("card border-l-4 p-4 space-y-2 animate-fade-in", cfg.borderCls)}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2 min-w-0">
          {cfg.icon}
          <p className="text-sm font-semibold text-slate-800 leading-snug truncate">
            {line.designation}
          </p>
        </div>
        <div className="shrink-0">
          <StatusBadge status={line.status} />
        </div>
      </div>

      <p className="text-xs text-slate-600 leading-relaxed">
        {line.message}
      </p>

      <div className="flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-slate-500">
        <span>
          Prix unitaire : <strong className="text-slate-700">{line.prix_unitaire.toFixed(2)} &euro;</strong>
        </span>
        <span>
          Ref. marche : {line.reference_prix_bas.toFixed(2)} &ndash; {line.reference_prix_haut.toFixed(2)} &euro;
          {line.reference_unite && ` / ${line.reference_unite}`}
        </span>
        <span>
          Ratio : <strong className={cn(
            line.ratio_vs_moyen < 0.8 ? "text-orange-600" :
            line.ratio_vs_moyen > 1.2 ? "text-red-600" : "text-green-600"
          )}>{(line.ratio_vs_moyen * 100).toFixed(0)}%</strong>
        </span>
      </div>
    </div>
  );
}

// -- Format currency helper --------------------------------------------------

function fmtEur(v: number): string {
  return v.toLocaleString("fr-FR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

// -- Skeleton ----------------------------------------------------------------

function DpgfSkeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      {/* Header skeleton */}
      <div className="card p-5">
        <div className="flex gap-3 mb-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-6 w-20 bg-slate-100 rounded-full" />
          ))}
        </div>
        <div className="h-3 bg-slate-100 rounded w-1/2" />
      </div>
      {/* Alert cards skeleton */}
      {[1, 2].map((i) => (
        <div key={i} className="card border-l-4 border-l-slate-200 p-4 space-y-2">
          <div className="h-4 bg-slate-200 rounded w-2/3" />
          <div className="h-3 bg-slate-100 rounded w-full" />
          <div className="h-3 bg-slate-100 rounded w-1/2" />
        </div>
      ))}
      {/* Table skeleton */}
      <div className="card p-0">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="flex gap-4 px-4 py-3 border-b border-slate-100">
            <div className="h-3 bg-slate-100 rounded w-1/3" />
            <div className="h-3 bg-slate-100 rounded w-16" />
            <div className="h-3 bg-slate-100 rounded w-24" />
            <div className="h-3 bg-slate-100 rounded w-12" />
            <div className="h-5 bg-slate-100 rounded-full w-20" />
          </div>
        ))}
      </div>
    </div>
  );
}

// -- Main component ----------------------------------------------------------

export function DpgfPricingTab({ projectId }: Props) {
  const { data, isLoading, isError } = useDpgfPricing(projectId);

  if (isLoading) return <DpgfSkeleton />;

  if (isError) {
    return (
      <div className="card p-8 flex flex-col items-center gap-3 text-center animate-fade-in">
        <AlertTriangle className="w-10 h-10 text-amber-400" />
        <p className="text-slate-600 font-medium">
          Impossible de charger l&apos;analyse tarifaire DPGF.
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

  const pricing = data as DpgfPricingData;

  // Empty state: no DPGF docs
  if ((!pricing.pricing_analysis || pricing.pricing_analysis.length === 0) && pricing.message) {
    return (
      <div className="card p-10 flex flex-col items-center gap-4 text-center animate-fade-in">
        <div className="w-14 h-14 rounded-2xl bg-slate-100 flex items-center justify-center">
          <FileX className="w-7 h-7 text-slate-400" />
        </div>
        <div className="space-y-1">
          <p className="font-semibold text-slate-700">
            Aucun document DPGF disponible
          </p>
          <p className="text-slate-400 text-sm max-w-sm">
            {pricing.message}
          </p>
        </div>
      </div>
    );
  }

  // Empty state: no data at all
  if (!pricing.pricing_analysis || pricing.pricing_analysis.length === 0) {
    return (
      <div className="card p-10 flex flex-col items-center gap-4 text-center animate-fade-in">
        <div className="w-14 h-14 rounded-2xl bg-slate-100 flex items-center justify-center">
          <BarChart3 className="w-7 h-7 text-slate-400" />
        </div>
        <div className="space-y-1">
          <p className="font-semibold text-slate-700">
            Aucune analyse tarifaire
          </p>
          <p className="text-slate-400 text-sm max-w-sm">
            Uploadez un DPGF ou BPU pour activer l&apos;intelligence tarifaire.
          </p>
        </div>
      </div>
    );
  }

  // Counts
  const lines = pricing.pricing_analysis;
  const nbSousEvalue = lines.filter((l) => l.status === "SOUS_EVALUE").length;
  const nbSurEvalue = lines.filter((l) => l.status === "SUR_EVALUE").length;
  const nbNormal = lines.filter((l) => l.status === "NORMAL").length;
  const nbInconnu = lines.filter((l) => l.status === "INCONNU").length;
  const alerts = pricing.alerts ?? lines.filter(
    (l) => l.status === "SOUS_EVALUE" || l.status === "SUR_EVALUE"
  );

  return (
    <div className="space-y-4 animate-fade-in">
      {/* -- Header card -- */}
      <div className="card p-5">
        <div className="flex flex-col sm:flex-row sm:items-center gap-5">
          {/* Big stat */}
          <div className="shrink-0 flex flex-col items-center">
            <div className="w-16 h-16 rounded-2xl bg-blue-100 flex items-center justify-center">
              <BarChart3 className="w-8 h-8 text-blue-700" />
            </div>
            <p className="text-xl font-bold text-slate-800 mt-2">
              {pricing.total_lines ?? lines.length}
            </p>
            <p className="text-[11px] text-slate-500 font-medium">
              postes analysés
            </p>
          </div>

          {/* Counters */}
          <div className="flex-1 space-y-3">
            <div className="flex flex-wrap gap-x-5 gap-y-2">
              <StatCounter
                label="Sous-évalués"
                count={nbSousEvalue}
                badgeCls="bg-orange-100 text-orange-800 border border-orange-200"
                icon={<TrendingDown className="w-3.5 h-3.5 text-orange-500" />}
              />
              <StatCounter
                label="Surévalués"
                count={nbSurEvalue}
                badgeCls="bg-red-100 text-red-800 border border-red-200"
                icon={<TrendingUp className="w-3.5 h-3.5 text-red-600" />}
              />
              <StatCounter
                label="Normaux"
                count={nbNormal}
                badgeCls="bg-green-100 text-green-800 border border-green-200"
                icon={<CheckCircle className="w-3.5 h-3.5 text-green-600" />}
              />
              {nbInconnu > 0 && (
                <StatCounter
                  label="Inconnus"
                  count={nbInconnu}
                  badgeCls="bg-slate-100 text-slate-600 border border-slate-200"
                  icon={<HelpCircle className="w-3.5 h-3.5 text-slate-400" />}
                />
              )}
            </div>

            {/* Alert count */}
            {alerts.length > 0 && (
              <div className="flex items-center gap-2">
                <Info className="w-4 h-4 text-amber-500" />
                <p className="text-xs text-amber-700 font-medium">
                  {alerts.length} alerte{alerts.length > 1 ? "s" : ""} tarifaire{alerts.length > 1 ? "s" : ""} détectée{alerts.length > 1 ? "s" : ""}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* -- Alerts section -- */}
      {alerts.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3 px-1">
            Alertes tarifaires ({alerts.length})
          </p>
          <div className="space-y-3">
            {alerts
              .sort((a, b) => {
                const order: PricingStatus[] = ["SUR_EVALUE", "SOUS_EVALUE", "NORMAL", "INCONNU"];
                return order.indexOf(a.status) - order.indexOf(b.status);
              })
              .map((line, i) => (
                <AlertCard key={i} line={line} />
              ))}
          </div>
        </div>
      )}

      {/* -- Full pricing table -- */}
      <div>
        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3 px-1">
          Détail des postes ({lines.length})
        </p>
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200">
                  <th className="text-left px-4 py-2.5 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                    Désignation
                  </th>
                  <th className="text-right px-4 py-2.5 text-xs font-semibold text-slate-500 uppercase tracking-wide whitespace-nowrap">
                    Prix unitaire
                  </th>
                  <th className="text-right px-4 py-2.5 text-xs font-semibold text-slate-500 uppercase tracking-wide whitespace-nowrap">
                    Réf. marché (bas - haut)
                  </th>
                  <th className="text-right px-4 py-2.5 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                    Ratio
                  </th>
                  <th className="text-center px-4 py-2.5 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                    Statut
                  </th>
                </tr>
              </thead>
              <tbody>
                {lines.map((line, i) => {
                  const cfg = STATUS_CONFIG[line.status] ?? STATUS_CONFIG.INCONNU;
                  return (
                    <tr
                      key={i}
                      className={cn(
                        "border-b border-slate-100 last:border-b-0 transition-colors",
                        cfg.rowCls,
                      )}
                    >
                      <td className="px-4 py-2.5 text-sm text-slate-800 font-medium max-w-xs">
                        <span className="line-clamp-2">{line.designation}</span>
                      </td>
                      <td className="px-4 py-2.5 text-sm text-slate-700 text-right whitespace-nowrap font-mono">
                        {fmtEur(line.prix_unitaire)} &euro;
                      </td>
                      <td className="px-4 py-2.5 text-xs text-slate-500 text-right whitespace-nowrap">
                        {fmtEur(line.reference_prix_bas)} &ndash; {fmtEur(line.reference_prix_haut)} &euro;
                        {line.reference_unite && (
                          <span className="text-slate-400 ml-0.5">/ {line.reference_unite}</span>
                        )}
                      </td>
                      <td className="px-4 py-2.5 text-right whitespace-nowrap">
                        <span
                          className={cn(
                            "text-xs font-bold",
                            line.ratio_vs_moyen < 0.8 ? "text-orange-600" :
                            line.ratio_vs_moyen > 1.2 ? "text-red-600" : "text-green-600"
                          )}
                        >
                          {(line.ratio_vs_moyen * 100).toFixed(0)}%
                        </span>
                      </td>
                      <td className="px-4 py-2.5 text-center">
                        <StatusBadge status={line.status} />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* -- Footer disclaimer -- */}
      <AIDisclaimer text="Référentiel indicatif 2024 (ajusté 2026) — les prix réels varient selon localisation, quantités et conjoncture. Ne se substitue pas à une estimation professionnelle." />
    </div>
  );
}
