"use client";

export const dynamic = "force-dynamic";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import {
  Plus, FolderOpen, TrendingUp, FileText,
  Calendar, CheckCircle, Clock, Archive, AlertCircle,
} from "lucide-react";
import { projectsApi } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { StatCardSkeleton } from "@/components/common/Skeleton";

// ── Types ──────────────────────────────────────────────────────────────
interface PipelineProject {
  id: string;
  title: string;
  buyer: string | null;
  submission_deadline: string | null;
  docs_count: number;
  reference?: string | null;
}

interface PipelineStats {
  columns: Record<string, PipelineProject[]>;
  stats: {
    total_projects: number;
    total_won: number;
    win_rate_pct: number;
    avg_market_size_eur: number | null;
  };
}

// ── Colonne Kanban config ──────────────────────────────────────────────
const COLUMNS = [
  {
    key: "draft",
    label: "Brouillon",
    icon: FileText,
    headerBg: "bg-slate-100",
    headerText: "text-slate-600",
    dotColor: "bg-slate-400",
    badgeBg: "bg-slate-100",
    badgeText: "text-slate-600",
    borderAccent: "border-t-slate-400",
  },
  {
    key: "processing",
    label: "En traitement",
    icon: Clock,
    headerBg: "bg-blue-50",
    headerText: "text-blue-700",
    dotColor: "bg-blue-500",
    badgeBg: "bg-blue-50",
    badgeText: "text-blue-700",
    borderAccent: "border-t-blue-500",
  },
  {
    key: "analyzing",
    label: "Analyse IA",
    icon: TrendingUp,
    headerBg: "bg-primary-50",
    headerText: "text-primary-700",
    dotColor: "bg-primary-600",
    badgeBg: "bg-primary-50",
    badgeText: "text-primary-700",
    borderAccent: "border-t-primary-600",
  },
  {
    key: "ready",
    label: "Prêt",
    icon: CheckCircle,
    headerBg: "bg-success-50",
    headerText: "text-success-700",
    dotColor: "bg-success-500",
    badgeBg: "bg-success-50",
    badgeText: "text-success-700",
    borderAccent: "border-t-success-500",
  },
  {
    key: "archived",
    label: "Archivé",
    icon: Archive,
    headerBg: "bg-slate-50",
    headerText: "text-slate-400",
    dotColor: "bg-slate-300",
    badgeBg: "bg-slate-50",
    badgeText: "text-slate-400",
    borderAccent: "border-t-slate-300",
  },
] as const;

// ── Stat Card ──────────────────────────────────────────────────────────
function StatCard({
  icon,
  label,
  value,
  gradient,
  sub,
}: {
  icon: React.ReactNode;
  label: string;
  value: number | string;
  gradient: string;
  sub?: string;
}) {
  return (
    <div className={`rounded-2xl border p-5 shadow-card animate-slide-up ${gradient}`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-2">{label}</p>
          <p className="text-3xl font-extrabold text-slate-900">{value}</p>
          {sub && <p className="text-xs text-slate-400 mt-1">{sub}</p>}
        </div>
        <div className="p-2.5 rounded-xl bg-white/70 shadow-sm">{icon}</div>
      </div>
    </div>
  );
}

// ── Kanban Card ────────────────────────────────────────────────────────
function KanbanCard({
  project,
  colKey,
}: {
  project: PipelineProject;
  colKey: string;
}) {
  const isUrgent = project.submission_deadline
    ? (new Date(project.submission_deadline).getTime() - Date.now()) < 7 * 86400000
    : false;

  const isAnalyzing = colKey === "analyzing";

  return (
    <Link
      href={`/projects/${project.id}`}
      className="card p-4 block hover:shadow-card-hover transition-all duration-150 group animate-fade-in"
    >
      {/* Titre */}
      <p className="font-semibold text-slate-900 text-sm leading-snug group-hover:text-primary-800 transition-colors line-clamp-2">
        {project.title}
      </p>

      {/* Acheteur */}
      <p className="text-xs text-slate-400 mt-1 truncate">
        {project.buyer ?? "Acheteur non renseigné"}
        {project.reference && (
          <span className="ml-1.5 text-slate-300">• {project.reference}</span>
        )}
      </p>

      {/* Footer de la carte */}
      <div className="flex items-center justify-between mt-3 pt-2.5 border-t border-slate-100">
        {/* Date limite */}
        {project.submission_deadline ? (
          <div
            className={`flex items-center gap-1 text-xs font-medium
              ${isUrgent ? "text-danger-600" : "text-slate-400"}`}
          >
            <Calendar className="w-3 h-3 flex-shrink-0" />
            <span>{formatDate(project.submission_deadline)}</span>
            {isUrgent && (
              <span className="badge-manquant text-[10px] py-0 px-1.5 ml-0.5">
                &lt;7j
              </span>
            )}
          </div>
        ) : (
          <span className="text-xs text-slate-300">Pas de date</span>
        )}

        {/* Compteur docs */}
        <div className="flex items-center gap-1 text-xs text-slate-400">
          {isAnalyzing && (
            <span className="w-1.5 h-1.5 rounded-full bg-primary-500 animate-pulse inline-block mr-0.5" />
          )}
          <FileText className="w-3 h-3" />
          <span>{project.docs_count}</span>
        </div>
      </div>
    </Link>
  );
}

// ── Colonne Kanban ─────────────────────────────────────────────────────
function KanbanColumn({
  colConfig,
  projects,
}: {
  colConfig: (typeof COLUMNS)[number];
  projects: PipelineProject[];
}) {
  const Icon = colConfig.icon;

  return (
    <div className="flex flex-col min-w-0 flex-1">
      {/* Header colonne */}
      <div
        className={`flex items-center justify-between px-3 py-2 rounded-xl mb-3
          border-t-2 ${colConfig.borderAccent} ${colConfig.headerBg}`}
      >
        <div className={`flex items-center gap-1.5 ${colConfig.headerText}`}>
          <Icon className="w-3.5 h-3.5" />
          <span className="text-xs font-semibold">{colConfig.label}</span>
        </div>
        <span
          className={`text-[11px] font-bold rounded-full px-2 py-0.5
            ${colConfig.badgeBg} ${colConfig.badgeText}`}
        >
          {projects.length}
        </span>
      </div>

      {/* Cartes */}
      <div className="flex flex-col gap-2 min-h-[120px]">
        {projects.length === 0 ? (
          <div className="flex-1 flex items-center justify-center text-xs text-slate-300
                          border-2 border-dashed border-slate-200 rounded-xl py-6">
            Aucun projet
          </div>
        ) : (
          projects.map((p) => (
            <KanbanCard key={p.id} project={p} colKey={colConfig.key} />
          ))
        )}
      </div>
    </div>
  );
}

// ── Skeleton Kanban ────────────────────────────────────────────────────
function KanbanSkeleton() {
  return (
    <div className="flex gap-4 overflow-x-auto pb-4">
      {COLUMNS.map((col) => (
        <div key={col.key} className="flex flex-col min-w-[220px] flex-1">
          <div className="h-9 bg-slate-100 rounded-xl mb-3 animate-pulse" />
          {[1, 2].map((i) => (
            <div key={i} className="h-24 bg-slate-100 rounded-2xl mb-2 animate-pulse" />
          ))}
        </div>
      ))}
    </div>
  );
}

// ── Empty State ────────────────────────────────────────────────────────
function PipelineEmptyState() {
  return (
    <div className="empty-state animate-fade-in">
      <div className="w-16 h-16 rounded-2xl bg-primary-50 flex items-center justify-center mx-auto mb-4">
        <FolderOpen className="w-8 h-8 text-primary-400" />
      </div>
      <h3 className="text-slate-700 font-semibold text-lg">Aucun projet dans le pipeline</h3>
      <p className="text-slate-400 text-sm mt-1 max-w-xs mx-auto">
        Créez votre premier projet pour commencer à suivre vos appels d&apos;offres.
      </p>
      <Link href="/projects/new" className="btn-primary-gradient inline-flex items-center gap-2 mt-6">
        <Plus className="w-4 h-4" /> Créer un projet
      </Link>
    </div>
  );
}

// ── Vue liste mobile ───────────────────────────────────────────────────
function MobileListView({ data }: { data: PipelineStats }) {
  const allProjects = COLUMNS.flatMap((col) =>
    (data?.columns?.[col.key] ?? []).map((p) => ({ ...p, colKey: col.key, colLabel: col.label }))
  );

  if (allProjects.length === 0) return <PipelineEmptyState />;

  return (
    <div className="space-y-2">
      {allProjects.map((project) => {
        const colConf = COLUMNS.find((c) => c.key === project.colKey)!;
        const isUrgent = project.submission_deadline
          ? (new Date(project.submission_deadline).getTime() - Date.now()) < 7 * 86400000
          : false;

        return (
          <Link
            key={project.id}
            href={`/projects/${project.id}`}
            className={`card flex items-center justify-between p-4 pl-0 border-l-4
              hover:shadow-card-hover transition-all duration-150 group animate-slide-up
              ${colConf.borderAccent.replace("border-t-", "border-l-")}`}
          >
            <div className="flex items-center gap-4 pl-5 min-w-0">
              <div className={`w-2 h-2 rounded-full flex-shrink-0 ${colConf.dotColor}`} />
              <div className="min-w-0">
                <p className="font-semibold text-slate-900 text-sm truncate group-hover:text-primary-800 transition-colors">
                  {project.title}
                </p>
                <p className="text-xs text-slate-400 mt-0.5 truncate">
                  {project.buyer ?? "Acheteur non renseigné"}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3 pl-4 flex-shrink-0">
              {project.submission_deadline && (
                <div className={`flex items-center gap-1 text-xs ${isUrgent ? "text-danger-600 font-medium" : "text-slate-400"}`}>
                  <Calendar className="w-3.5 h-3.5" />
                  {formatDate(project.submission_deadline)}
                  {isUrgent && (
                    <span className="badge-manquant text-[10px] py-0 px-1.5">Urgent</span>
                  )}
                </div>
              )}
              <span className={`badge text-xs ${colConf.badgeBg} ${colConf.badgeText}`}>
                {colConf.label}
              </span>
            </div>
          </Link>
        );
      })}
    </div>
  );
}

// ── Main Page ──────────────────────────────────────────────────────────
export default function PipelinePage() {
  const { data, isLoading } = useQuery<PipelineStats>({
    queryKey: ["pipeline"],
    queryFn: () => projectsApi.pipeline().then((r) => r.data),
  });

  const totalProjects = data?.stats.total_projects ?? 0;
  const winRate = data?.stats.win_rate_pct ?? 0;
  const inProgress =
    (data?.columns?.processing?.length ?? 0) + (data?.columns?.analyzing?.length ?? 0);

  return (
    <div className="p-6 md:p-8 max-w-screen-xl mx-auto space-y-8">
      {/* ── Header ── */}
      <div className="flex items-start justify-between animate-fade-in">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Pipeline AO</h1>
          <p className="text-slate-400 text-sm mt-0.5">
            Vue d&apos;ensemble de vos appels d&apos;offres
          </p>
        </div>
        <Link
          href="/projects/new"
          className="btn-primary-gradient flex items-center gap-2 shadow-md"
        >
          <Plus className="w-4 h-4" />
          <span className="hidden sm:inline">Nouveau projet</span>
          <span className="sm:hidden">Nouveau</span>
        </Link>
      </div>

      {/* ── Stats ── */}
      {isLoading ? (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => <StatCardSkeleton key={i} />)}
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <StatCard
            icon={<FolderOpen className="w-5 h-5 text-primary-700" />}
            label="Total projets"
            value={totalProjects}
            gradient="bg-gradient-to-br from-primary-50 to-primary-100 border-primary-200"
          />
          <StatCard
            icon={<TrendingUp className="w-5 h-5 text-success-600" />}
            label="Taux de réussite"
            value={totalProjects > 0 ? `${winRate}%` : "—"}
            gradient="bg-gradient-to-br from-success-50 to-emerald-50 border-success-200"
            sub={totalProjects > 0 ? `${data?.stats.total_won ?? 0} prêts sur ${totalProjects}` : "Pas encore de données"}
          />
          <StatCard
            icon={<Clock className="w-5 h-5 text-warning-600" />}
            label="En cours"
            value={inProgress}
            gradient="bg-gradient-to-br from-warning-50 to-amber-50 border-warning-200"
            sub="Traitement + Analyse IA"
          />
        </div>
      )}

      {/* ── Kanban (desktop) ── */}
      <div className="hidden md:block">
        {isLoading ? (
          <KanbanSkeleton />
        ) : totalProjects === 0 ? (
          <PipelineEmptyState />
        ) : (
          <div className="flex gap-4 overflow-x-auto pb-4 items-start">
            {COLUMNS.map((col) => (
              <KanbanColumn
                key={col.key}
                colConfig={col}
                projects={data?.columns[col.key] ?? []}
              />
            ))}
          </div>
        )}
      </div>

      {/* ── Liste verticale (mobile) ── */}
      <div className="md:hidden">
        {isLoading ? (
          <div className="space-y-2">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-16 bg-slate-100 rounded-2xl animate-pulse" />
            ))}
          </div>
        ) : data ? (
          <MobileListView data={data} />
        ) : (
          <PipelineEmptyState />
        )}
      </div>
    </div>
  );
}
