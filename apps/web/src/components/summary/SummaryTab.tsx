"use client";
import {
  AlertTriangle, ShieldAlert, ShieldCheck, Shield,
  Zap, Building2, Calendar, Euro, MapPin, Eye
} from "lucide-react";
import { CitationTooltip } from "@/components/ui/CitationTooltip";

interface Citation { doc: string; page: number; quote: string; }
interface Summary {
  project_overview: {
    title: string; buyer: string; scope: string; location: string;
    deadline_submission: string; site_visit_required: boolean;
    market_type: string | null; estimated_budget: string | null;
  };
  key_points: Array<{ label: string; value: string; citations: Citation[] }>;
  risks: Array<{ risk: string; severity: "high" | "medium" | "low"; why: string; citations: Citation[] }>;
  actions_next_48h: Array<{ action: string; owner_role: string; priority: "P0" | "P1" | "P2" }>;
}

// ── Risk config avec icônes shield ─────────────────────────────────────
const RISK_CONFIG = {
  high: {
    icon: <ShieldAlert className="w-4 h-4" />,
    label: "Éliminatoire",
    cardClass: "risk-row-high",
    badgeClass: "badge-critique",
    barClass: "bg-danger-500",
    barWidth: "w-full",
  },
  medium: {
    icon: <Shield className="w-4 h-4" />,
    label: "Majeur",
    cardClass: "risk-row-medium",
    badgeClass: "badge-important",
    barClass: "bg-warning-500",
    barWidth: "w-2/3",
  },
  low: {
    icon: <ShieldCheck className="w-4 h-4" />,
    label: "Mineur",
    cardClass: "border-l-4 border-l-success-500 bg-success-50/30",
    badgeClass: "badge bg-success-100 text-success-700",
    barClass: "bg-success-500",
    barWidth: "w-1/3",
  },
};

const PRIORITY_CONFIG = {
  P0: { label: "P0 — Urgent",   bg: "bg-danger-600",  text: "text-white",       dot: "bg-danger-600" },
  P1: { label: "P1 — Important",bg: "bg-warning-600", text: "text-white",       dot: "bg-warning-500" },
  P2: { label: "P2 — Standard", bg: "bg-slate-200",   text: "text-slate-700",   dot: "bg-slate-400" },
};

// ── Overview info cards ────────────────────────────────────────────────
function OverviewCard({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="flex items-start gap-3 p-3.5 bg-white rounded-xl border border-primary-100">
      <div className="p-1.5 bg-primary-50 rounded-lg text-primary-700 flex-shrink-0">{icon}</div>
      <div className="min-w-0">
        <p className="text-xs text-slate-400 mb-0.5">{label}</p>
        <p className="text-sm font-semibold text-slate-800 truncate">{value || "—"}</p>
      </div>
    </div>
  );
}

// ── Main Component ─────────────────────────────────────────────────────
export function SummaryTab({ summary }: { summary: Summary }) {
  const { project_overview: po, key_points = [], risks = [], actions_next_48h = [] } = summary;

  const riskCounts = {
    high: risks.filter(r => r.severity === "high").length,
    medium: risks.filter(r => r.severity === "medium").length,
    low: risks.filter(r => r.severity === "low").length,
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* ── Vue d'ensemble du marché ── */}
      <section>
        <h3 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
          <Building2 className="w-4 h-4 text-primary-600" />
          Vue d&apos;ensemble du marché
        </h3>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-3">
          <OverviewCard icon={<Building2 className="w-3.5 h-3.5" />} label="Acheteur" value={po.buyer} />
          <OverviewCard icon={<Eye className="w-3.5 h-3.5" />} label="Type marché" value={po.market_type ?? "—"} />
          <OverviewCard icon={<Calendar className="w-3.5 h-3.5" />} label="Date limite" value={po.deadline_submission} />
          <OverviewCard icon={<Euro className="w-3.5 h-3.5" />} label="Budget estimé" value={po.estimated_budget ?? "Non précisé"} />
        </div>

        {po.location && (
          <div className="flex items-center gap-2 text-xs text-slate-500 mb-2">
            <MapPin className="w-3.5 h-3.5 text-slate-400" />
            {po.location}
          </div>
        )}

        {po.scope && (
          <div className="bg-primary-50 border border-primary-100 rounded-xl p-4">
            <p className="text-xs font-medium text-primary-700 uppercase tracking-wide mb-1">Périmètre</p>
            <p className="text-sm text-slate-700 leading-relaxed">{po.scope}</p>
          </div>
        )}

        {po.site_visit_required && (
          <div className="mt-3 flex items-center gap-2 text-amber-700 bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 text-sm">
            <AlertTriangle className="w-4 h-4 flex-shrink-0" />
            <span><strong>Visite de site obligatoire</strong> — Attestation de visite à obtenir impérativement</span>
          </div>
        )}
      </section>

      {/* ── Points clés ── */}
      {key_points.length > 0 && (
        <section>
          <h3 className="text-sm font-semibold text-slate-700 mb-3">Points clés</h3>
          <div className="card overflow-hidden">
            <table className="w-full text-xs">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-100">
                  <th className="text-left px-4 py-3 font-semibold text-slate-500 w-40">Point</th>
                  <th className="text-left px-4 py-3 font-semibold text-slate-500">Valeur</th>
                  <th className="text-left px-4 py-3 font-semibold text-slate-500 w-24">Source</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {key_points.map((kp, i) => (
                  <tr key={i} className="hover:bg-slate-50/70 transition-colors">
                    <td className="px-4 py-3 font-semibold text-slate-600">{kp.label}</td>
                    <td className="px-4 py-3 text-slate-800 font-medium">{kp.value}</td>
                    <td className="px-4 py-3"><CitationTooltip citations={kp.citations} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* ── Risques ── */}
      {risks.length > 0 && (
        <section>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-danger-500" />
              Risques identifiés
            </h3>
            {/* Pills de résumé */}
            <div className="flex items-center gap-2">
              {riskCounts.high > 0 && (
                <span className="badge-critique">{riskCounts.high} éliminatoire{riskCounts.high > 1 ? "s" : ""}</span>
              )}
              {riskCounts.medium > 0 && (
                <span className="badge-important">{riskCounts.medium} majeur{riskCounts.medium > 1 ? "s" : ""}</span>
              )}
              {riskCounts.low > 0 && (
                <span className="badge bg-success-100 text-success-700">{riskCounts.low} mineur{riskCounts.low > 1 ? "s" : ""}</span>
              )}
            </div>
          </div>

          <div className="space-y-2">
            {risks.map((r, i) => {
              const conf = RISK_CONFIG[r.severity] ?? RISK_CONFIG.low;
              return (
                <div key={i} className={`rounded-xl p-4 transition-all duration-100 ${conf.cardClass}`}>
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <div className="flex items-center gap-2 min-w-0">
                      <span className={`flex-shrink-0 ${r.severity === "high" ? "text-danger-600" : r.severity === "medium" ? "text-warning-600" : "text-success-600"}`}>
                        {conf.icon}
                      </span>
                      <p className="font-semibold text-sm text-slate-900">{r.risk}</p>
                    </div>
                    <span className={`flex-shrink-0 ${conf.badgeClass}`}>{conf.label}</span>
                  </div>

                  {/* Barre horizontale colorée (severity indicator) */}
                  <div className="h-1 bg-black/5 rounded-full mb-2">
                    <div className={`h-full rounded-full ${conf.barClass} ${conf.barWidth} transition-all`} />
                  </div>

                  <p className="text-xs text-slate-600 leading-relaxed">{r.why}</p>
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* ── Actions 48h ── */}
      {actions_next_48h.length > 0 && (
        <section>
          <h3 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
            <Zap className="w-4 h-4 text-primary-600" />
            Actions à prendre sous 48h
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {actions_next_48h.map((a, i) => {
              const pConf = PRIORITY_CONFIG[a.priority] ?? PRIORITY_CONFIG.P2;
              return (
                <div key={i} className="card p-4 flex items-start gap-3 hover:shadow-card-hover transition-shadow duration-150">
                  <div className={`w-2 h-2 rounded-full flex-shrink-0 mt-1.5 ${pConf.dot}`} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${pConf.bg} ${pConf.text}`}>
                        {a.priority}
                      </span>
                      <span className="text-xs text-slate-400">{a.owner_role}</span>
                    </div>
                    <p className="text-sm font-medium text-slate-800 leading-snug">{a.action}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      )}
    </div>
  );
}
