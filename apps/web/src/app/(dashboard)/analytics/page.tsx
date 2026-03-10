"use client";

export const dynamic = "force-dynamic";

import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  FolderOpen,
  FileText,
  TrendingUp,
  Clock,
  BarChart2,
  Activity,
} from "lucide-react";
import { analyticsApi, billingApi } from "@/lib/api";
import UsageBar from "@/components/billing/UsageBar";
import { BillingUsage } from "@/stores/billing";

// ── Types ──────────────────────────────────────────────────────────────────

interface OrgStats {
  total_projects: number;
  projects_by_status: Record<string, number>;
  total_documents: number;
  avg_docs_per_project: number;
  projects_this_month: number;
  most_common_doc_types: string[];
  avg_analysis_time_minutes: number;
}

interface ActivityEntry {
  date: string;
  projects_created: number;
  documents_uploaded: number;
}

// ── Fetchers ───────────────────────────────────────────────────────────────

const fetchStats = async (): Promise<OrgStats> => {
  const res = await analyticsApi.getStats();
  return res.data;
};

const fetchActivity = async (): Promise<ActivityEntry[]> => {
  const res = await analyticsApi.getActivity();
  return res.data.series;
};

const fetchUsage = async (): Promise<BillingUsage> => {
  const res = await billingApi.getUsage();
  return res.data;
};

// ── Composants ─────────────────────────────────────────────────────────────

function StatCard({
  icon,
  label,
  value,
  sub,
  gradient,
}: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  sub?: string;
  gradient: string;
}) {
  return (
    <div className={`rounded-2xl border p-5 shadow-sm ${gradient}`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">{label}</p>
          <p className="text-3xl font-extrabold text-gray-900">{value}</p>
          {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
        </div>
        <div className="p-2.5 rounded-xl bg-white/70 shadow-sm text-gray-600">{icon}</div>
      </div>
    </div>
  );
}

const STATUS_COLORS: Record<string, { bar: string; text: string; label: string }> = {
  ready:     { bar: "bg-emerald-500", text: "text-emerald-700", label: "Terminés" },
  analyzing: { bar: "bg-blue-500",    text: "text-blue-700",    label: "En analyse" },
  draft:     { bar: "bg-slate-400",   text: "text-slate-600",   label: "Brouillons" },
  archived:  { bar: "bg-gray-300",    text: "text-gray-500",    label: "Archivés" },
};

const DOC_TYPE_COLORS: Record<string, string> = {
  RC:    "bg-blue-500",
  CCTP:  "bg-indigo-500",
  CCAP:  "bg-purple-500",
  DPGF:  "bg-amber-500",
  BPU:   "bg-orange-500",
  AE:    "bg-green-500",
  ATTRI: "bg-emerald-500",
  AUTRES: "bg-slate-400",
};

function StatusDistribution({
  statuses,
  total,
}: {
  statuses: Record<string, number>;
  total: number;
}) {
  const entries = Object.entries(statuses)
    .filter(([, count]) => count > 0)
    .sort((a, b) => b[1] - a[1]);

  if (entries.length === 0) {
    return <p className="text-sm text-gray-400">Aucun projet.</p>;
  }

  return (
    <div className="space-y-3">
      {entries.map(([status, count]) => {
        const conf = STATUS_COLORS[status] ?? { bar: "bg-gray-300", text: "text-gray-500", label: status };
        const pct = total > 0 ? Math.round((count / total) * 100) : 0;
        return (
          <div key={status}>
            <div className="flex items-center justify-between mb-1">
              <span className={`text-sm font-medium ${conf.text}`}>{conf.label}</span>
              <span className="text-xs text-gray-400">
                {count} projet{count > 1 ? "s" : ""} — {pct}%
              </span>
            </div>
            <div className="h-2.5 bg-gray-100 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-700 ease-out ${conf.bar}`}
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

function ActivityChart({ series }: { series: ActivityEntry[] }) {
  const maxProjects = Math.max(...series.map((s) => s.projects_created), 1);
  const maxDocs = Math.max(...series.map((s) => s.documents_uploaded), 1);
  const maxVal = Math.max(maxProjects, maxDocs, 1);

  // Afficher seulement les 30 derniers jours, regroupés en semaines pour la lisibilité
  // Si series > 30, tronquer ; sinon afficher tous
  const displaySeries = series.slice(-30);

  // Pour les labels : afficher 1 date sur 5
  const labelStep = Math.max(1, Math.floor(displaySeries.length / 6));

  return (
    <div>
      <div className="flex items-end gap-1 h-36 border-b border-gray-200 pb-1">
        {displaySeries.map((entry, idx) => {
          const projH = Math.round((entry.projects_created / maxVal) * 100);
          const docH = Math.round((entry.documents_uploaded / maxVal) * 100);
          const hasActivity = entry.projects_created > 0 || entry.documents_uploaded > 0;

          return (
            <div
              key={entry.date}
              className="flex-1 flex flex-col items-center justify-end gap-0.5 group relative"
              title={`${entry.date} — ${entry.projects_created} projets, ${entry.documents_uploaded} docs`}
            >
              {/* Tooltip */}
              {hasActivity && (
                <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 z-10 hidden group-hover:flex
                  flex-col items-center bg-gray-900 text-white text-[10px] rounded-lg px-2 py-1.5 whitespace-nowrap shadow-lg">
                  <span className="font-semibold">{entry.date}</span>
                  <span>{entry.projects_created} proj. / {entry.documents_uploaded} docs</span>
                  <div className="absolute top-full left-1/2 -translate-x-1/2 w-0 h-0
                    border-l-4 border-r-4 border-t-4 border-l-transparent border-r-transparent border-t-gray-900" />
                </div>
              )}

              {/* Barres empilées */}
              <div className="w-full flex flex-col justify-end gap-0.5">
                {entry.documents_uploaded > 0 && (
                  <div
                    className="w-full bg-amber-400 rounded-sm transition-all duration-500"
                    style={{ height: `${Math.max(docH, 3)}%`, minHeight: "3px" }}
                  />
                )}
                {entry.projects_created > 0 && (
                  <div
                    className="w-full bg-blue-600 rounded-sm transition-all duration-500"
                    style={{ height: `${Math.max(projH, 3)}%`, minHeight: "3px" }}
                  />
                )}
                {!hasActivity && (
                  <div className="w-full bg-gray-100 rounded-sm" style={{ height: "3px" }} />
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Labels dates */}
      <div className="flex items-start mt-1" style={{ gap: "0" }}>
        {displaySeries.map((entry, idx) => {
          if (idx % labelStep !== 0 && idx !== displaySeries.length - 1) {
            return <div key={entry.date} className="flex-1" />;
          }
          const d = new Date(entry.date);
          const label = `${d.getDate()}/${d.getMonth() + 1}`;
          return (
            <div key={entry.date} className="flex-1 text-[9px] text-gray-400 text-center">
              {label}
            </div>
          );
        })}
      </div>

      {/* Légende */}
      <div className="flex items-center gap-4 mt-3">
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-sm bg-blue-600" />
          <span className="text-xs text-gray-500">Projets créés</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-sm bg-amber-400" />
          <span className="text-xs text-gray-500">Documents uploadés</span>
        </div>
      </div>
    </div>
  );
}

// ── Page principale ────────────────────────────────────────────────────────

export default function AnalyticsPage() {
  const { data: stats, isLoading: loadingStats } = useQuery({
    queryKey: ["analytics", "stats"],
    queryFn: fetchStats,
    staleTime: 5 * 60 * 1000,
  });

  const { data: activity = [], isLoading: loadingActivity } = useQuery({
    queryKey: ["analytics", "activity"],
    queryFn: fetchActivity,
    staleTime: 5 * 60 * 1000,
  });

  const { data: usage, isLoading: loadingUsage } = useQuery({
    queryKey: ["billing", "usage"],
    queryFn: fetchUsage,
    staleTime: 5 * 60 * 1000,
  });

  const isLoading = loadingStats || loadingActivity;

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 space-y-8 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Analytics & Activite</h1>
        <p className="text-gray-500 mt-1 text-sm">
          Suivi de votre activité, utilisation des quotas et répartition des projets.
        </p>
      </div>

      {/* Stat cards */}
      {isLoading ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-28 bg-gray-100 rounded-2xl animate-pulse" />
          ))}
        </div>
      ) : stats ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard
            icon={<FolderOpen className="w-5 h-5" />}
            label="Total projets"
            value={stats.total_projects}
            gradient="bg-gradient-to-br from-blue-50 to-blue-100 border border-blue-200"
          />
          <StatCard
            icon={<FileText className="w-5 h-5" />}
            label="Documents analysés"
            value={stats.total_documents}
            sub={`Moy. ${stats.avg_docs_per_project} / projet`}
            gradient="bg-gradient-to-br from-indigo-50 to-indigo-100 border border-indigo-200"
          />
          <StatCard
            icon={<TrendingUp className="w-5 h-5" />}
            label="Projets ce mois"
            value={stats.projects_this_month}
            gradient="bg-gradient-to-br from-emerald-50 to-emerald-100 border border-emerald-200"
          />
          <StatCard
            icon={<Clock className="w-5 h-5" />}
            label="Durée moy. analyse"
            value={
              stats.avg_analysis_time_minutes > 0
                ? `${stats.avg_analysis_time_minutes} min`
                : "—"
            }
            gradient="bg-gradient-to-br from-amber-50 to-amber-100 border border-amber-200"
          />
        </div>
      ) : null}

      {/* Graphique activité + Répartition statuts */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Graphique 30 jours */}
        <div className="md:col-span-2 bg-white border border-gray-100 rounded-2xl p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-4">
            <Activity className="w-4 h-4 text-blue-600" />
            <h2 className="text-sm font-semibold text-gray-800">Activite — 30 derniers jours</h2>
          </div>
          {loadingActivity ? (
            <div className="h-36 bg-gray-100 rounded-xl animate-pulse" />
          ) : activity.length > 0 ? (
            <ActivityChart series={activity} />
          ) : (
            <p className="text-sm text-gray-400 text-center py-12">Aucune activité sur cette période.</p>
          )}
        </div>

        {/* Répartition par statut */}
        <div className="bg-white border border-gray-100 rounded-2xl p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-4">
            <BarChart2 className="w-4 h-4 text-indigo-600" />
            <h2 className="text-sm font-semibold text-gray-800">Repartition par statut</h2>
          </div>
          {loadingStats ? (
            <div className="space-y-3">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="h-8 bg-gray-100 rounded animate-pulse" />
              ))}
            </div>
          ) : stats ? (
            <StatusDistribution
              statuses={stats.projects_by_status}
              total={stats.total_projects}
            />
          ) : null}
        </div>
      </div>

      {/* Types de documents fréquents */}
      {stats && stats.most_common_doc_types.length > 0 && (
        <div className="bg-white border border-gray-100 rounded-2xl p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-4">
            <FileText className="w-4 h-4 text-amber-600" />
            <h2 className="text-sm font-semibold text-gray-800">Types de documents les plus fréquents</h2>
          </div>
          <div className="flex flex-wrap gap-2">
            {stats.most_common_doc_types.map((type, idx) => {
              const color = DOC_TYPE_COLORS[type] ?? "bg-slate-400";
              return (
                <div key={type} className="flex items-center gap-2 bg-gray-50 border border-gray-200 rounded-xl px-3 py-2">
                  <div className={`w-2 h-2 rounded-full ${color}`} />
                  <span className="text-sm font-semibold text-gray-700">{type}</span>
                  {idx === 0 && (
                    <span className="text-[10px] bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded-full font-medium">
                      Le plus fréquent
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Utilisation quota */}
      <div className="bg-white border border-gray-100 rounded-2xl p-5 shadow-sm">
        <div className="flex items-center gap-2 mb-4">
          <BarChart2 className="w-4 h-4 text-blue-600" />
          <h2 className="text-sm font-semibold text-gray-800">Utilisation quota ce mois</h2>
        </div>
        {loadingUsage ? (
          <div className="h-24 bg-gray-100 rounded-xl animate-pulse" />
        ) : usage ? (
          <UsageBar usage={usage} />
        ) : (
          <p className="text-sm text-gray-400">Impossible de charger l'utilisation.</p>
        )}
      </div>
    </div>
  );
}
