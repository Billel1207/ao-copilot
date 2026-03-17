"use client";

import { useCashflowSimulation } from "@/hooks/useAnalysis";
import { AlertTriangle, Info, Loader2, TrendingDown, TrendingUp, Wallet, FileWarning } from "lucide-react";
import AIDisclaimer from "@/components/ui/AIDisclaimer";

interface Props {
  projectId: string;
}

const RISK_BADGE: Record<string, { bg: string; text: string }> = {
  FAIBLE: { bg: "bg-green-100", text: "text-green-800" },
  "MODÉRÉ": { bg: "bg-amber-100", text: "text-amber-800" },
  "ÉLEVÉ": { bg: "bg-orange-100", text: "text-orange-800" },
  CRITIQUE: { bg: "bg-red-100", text: "text-red-800" },
  INCONNU: { bg: "bg-slate-100", text: "text-slate-600 dark:text-slate-400" },
};

function KpiCard({ label, value, unit, icon, color }: {
  label: string; value: string | number; unit?: string;
  icon: React.ReactNode; color: string;
}) {
  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl border dark:border-slate-700 p-4 flex items-start gap-3">
      <div className={`p-2 rounded-lg ${color}`}>{icon}</div>
      <div>
        <p className="text-xs text-slate-500 dark:text-slate-400 mb-0.5">{label}</p>
        <p className="text-lg font-bold text-slate-800 dark:text-slate-100">
          {typeof value === "number" ? value.toLocaleString("fr-FR") : value}
          {unit && <span className="text-sm font-normal text-slate-500 dark:text-slate-400 ml-1">{unit}</span>}
        </p>
      </div>
    </div>
  );
}

function CashFlowChart({ data }: { data: any[] }) {
  if (!data || data.length === 0) return null;

  const maxAbs = Math.max(
    ...data.map((m) => Math.abs(m.solde_cumule || 0)),
    1
  );

  return (
    <div className="bg-white dark:bg-slate-900 rounded-xl border dark:border-slate-700 overflow-hidden">
      <div className="px-4 py-3 border-b dark:border-slate-700 bg-slate-50 dark:bg-slate-800">
        <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300">Courbe de trésorerie cumulée</h4>
      </div>
      <div className="p-4">
        <div className="flex items-end gap-1 h-48 overflow-x-auto">
          {data.map((m, i) => {
            const val = m.solde_cumule || 0;
            const height = Math.abs(val) / maxAbs * 100;
            const isNeg = val < 0;
            return (
              <div
                key={i}
                className="flex flex-col items-center flex-shrink-0"
                style={{ minWidth: data.length > 20 ? 20 : 32 }}
              >
                {/* Bar container with vertical centering */}
                <div className="relative h-40 w-full flex flex-col justify-center">
                  {/* Positive bars grow up from center */}
                  <div className="h-1/2 flex items-end justify-center">
                    {!isNeg && (
                      <div
                        className="w-full max-w-[24px] mx-auto rounded-t bg-emerald-400 transition-all hover:bg-emerald-500"
                        style={{ height: `${height}%` }}
                        title={`M${m.mois}: ${val.toLocaleString("fr-FR")} €`}
                      />
                    )}
                  </div>
                  {/* Zero line */}
                  <div className="h-px bg-slate-300 dark:bg-slate-600 w-full" />
                  {/* Negative bars grow down from center */}
                  <div className="h-1/2 flex items-start justify-center">
                    {isNeg && (
                      <div
                        className="w-full max-w-[24px] mx-auto rounded-b bg-red-400 transition-all hover:bg-red-500"
                        style={{ height: `${height}%` }}
                        title={`M${m.mois}: ${val.toLocaleString("fr-FR")} €`}
                      />
                    )}
                  </div>
                </div>
                <span className="text-[9px] text-slate-400 dark:text-slate-500 mt-1">
                  {m.mois === 0 ? "Av" : m.mois}
                </span>
              </div>
            );
          })}
        </div>
        <div className="flex items-center gap-4 mt-3 text-[10px] text-slate-500 dark:text-slate-400">
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded bg-emerald-400" /> Positif
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded bg-red-400" /> Négatif
          </span>
        </div>
      </div>
    </div>
  );
}

function MonthlyTable({ data }: { data: any[] }) {
  if (!data || data.length === 0) return null;

  return (
    <div className="bg-white dark:bg-slate-900 rounded-xl border dark:border-slate-700 overflow-hidden">
      <div className="px-4 py-3 border-b dark:border-slate-700 bg-slate-50 dark:bg-slate-800">
        <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300">Détail mensuel</h4>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead className="bg-slate-50 dark:bg-slate-800">
            <tr>
              <th className="text-left px-3 py-2 text-slate-500 dark:text-slate-400">Mois</th>
              <th className="text-right px-3 py-2 text-slate-500 dark:text-slate-400">Travaux HT</th>
              <th className="text-right px-3 py-2 text-slate-500 dark:text-slate-400">Dépenses</th>
              <th className="text-right px-3 py-2 text-slate-500 dark:text-slate-400">Encaissements</th>
              <th className="text-right px-3 py-2 text-slate-500 dark:text-slate-400">Solde mensuel</th>
              <th className="text-right px-3 py-2 text-slate-500 dark:text-slate-400">Cumulé</th>
            </tr>
          </thead>
          <tbody className="divide-y dark:divide-slate-700">
            {data.map((m, i) => (
              <tr
                key={i}
                className={m.solde_cumule < 0 ? "bg-red-50 dark:bg-red-900/20" : ""}
              >
                <td className="px-3 py-2 text-slate-700 dark:text-slate-300 font-medium">{m.label}</td>
                <td className="px-3 py-2 text-right text-slate-600 dark:text-slate-400">
                  {(m.travaux_realises_ht || 0).toLocaleString("fr-FR")}
                </td>
                <td className="px-3 py-2 text-right text-red-600">
                  {m.depenses_ht > 0 ? `-${m.depenses_ht.toLocaleString("fr-FR")}` : "—"}
                </td>
                <td className="px-3 py-2 text-right text-emerald-600">
                  {m.encaissement_ht > 0 ? `+${m.encaissement_ht.toLocaleString("fr-FR")}` : "—"}
                </td>
                <td className={`px-3 py-2 text-right font-medium ${m.solde_mensuel >= 0 ? "text-emerald-700" : "text-red-700"}`}>
                  {m.solde_mensuel.toLocaleString("fr-FR")}
                </td>
                <td className={`px-3 py-2 text-right font-bold ${m.solde_cumule >= 0 ? "text-emerald-700" : "text-red-700"}`}>
                  {m.solde_cumule.toLocaleString("fr-FR")}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default function CashFlowTab({ projectId }: Props) {
  const { data, isLoading, error } = useCashflowSimulation(projectId);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="w-6 h-6 animate-spin text-blue-500 mr-2" />
        <span className="text-sm text-slate-500 dark:text-slate-400">Simulation trésorerie en cours...</span>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="text-center py-12 text-slate-500 dark:text-slate-400">
        <FileWarning className="w-10 h-10 mx-auto mb-2 text-slate-400 dark:text-slate-500" />
        <p className="text-sm">Erreur lors de la simulation de trésorerie.</p>
      </div>
    );
  }

  const riskCfg = RISK_BADGE[data.risk_level] || RISK_BADGE.INCONNU;

  return (
    <div className="space-y-6">
      {/* Header avec risk level */}
      <div className="bg-white dark:bg-slate-900 rounded-xl border dark:border-slate-700 p-6">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-100 mb-2">Simulation Trésorerie</h3>
            <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">{data.resume}</p>
            {!data.source_ae && (
              <div className="mt-3 flex items-center gap-2 text-xs text-amber-600 bg-amber-50 px-3 py-2 rounded-lg">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                <span>{data.message}</span>
              </div>
            )}
          </div>
          <span
            className={`ml-4 px-3 py-1.5 rounded-full text-sm font-bold ${riskCfg.bg} ${riskCfg.text}`}
            aria-label={`Niveau de risque tresorerie : ${data.risk_level}`}
          >
            {data.risk_level}
          </span>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          label="Montant marché HT"
          value={data.montant_total_ht || 0}
          unit="EUR"
          icon={<Wallet className="w-5 h-5 text-blue-600" />}
          color="bg-blue-50"
        />
        <KpiCard
          label="BFR estimé"
          value={data.bfr_eur || 0}
          unit="EUR"
          icon={<TrendingDown className="w-5 h-5 text-red-600" />}
          color="bg-red-50"
        />
        <KpiCard
          label="Creux trésorerie max"
          value={data.peak_negative_cash || 0}
          unit="EUR"
          icon={<TrendingDown className="w-5 h-5 text-orange-600" />}
          color="bg-orange-50"
        />
        <KpiCard
          label="Mois en tension"
          value={data.nb_tension_months || 0}
          unit={`/ ${data.duree_mois || 0}`}
          icon={<AlertTriangle className="w-5 h-5 text-amber-600" />}
          color="bg-amber-50"
        />
      </div>

      {/* Impacts financiers */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white dark:bg-slate-800 rounded-xl border dark:border-slate-700 p-4">
          <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">Impact avance forfaitaire</p>
          <p className="text-lg font-bold text-emerald-700">
            +{(data.avance_impact_eur || 0).toLocaleString("fr-FR")} EUR
          </p>
          <p className="text-[10px] text-slate-400 dark:text-slate-500 mt-1">CCAG Art. 14.1 — améliore la trésorerie</p>
        </div>
        <div className="bg-white dark:bg-slate-800 rounded-xl border dark:border-slate-700 p-4">
          <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">Impact retenue garantie</p>
          <p className="text-lg font-bold text-red-700">
            -{(data.retenue_impact_eur || 0).toLocaleString("fr-FR")} EUR
          </p>
          <p className="text-[10px] text-slate-400 dark:text-slate-500 mt-1">CCAG Art. 14.3 — libérée après GPA (12 mois)</p>
        </div>
        <div className="bg-white dark:bg-slate-800 rounded-xl border dark:border-slate-700 p-4">
          <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">Pénalités potentielles (30j retard)</p>
          <p className="text-lg font-bold text-orange-700">
            -{(data.penalite_impact_30j_eur || 0).toLocaleString("fr-FR")} EUR
          </p>
          <p className="text-[10px] text-slate-400 dark:text-slate-500 mt-1">CCAG Art. 19.1 — 1/3000e par jour</p>
        </div>
      </div>

      {/* Chart */}
      <CashFlowChart data={data.monthly_cashflow || []} />

      {/* Monthly table */}
      <MonthlyTable data={data.monthly_cashflow || []} />

      {/* Footer disclaimer */}
      <AIDisclaimer text="Simulation de trésorerie indicative basée sur les données contractuelles — ne se substitue pas à un conseil financier professionnel." />
    </div>
  );
}
