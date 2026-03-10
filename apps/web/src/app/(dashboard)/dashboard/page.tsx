"use client";

export const dynamic = "force-dynamic";
import Link from "next/link";
import {
  Plus, FolderOpen, Clock, CheckCircle, AlertCircle,
  FileText, TrendingUp, Calendar, ChevronRight
} from "lucide-react";
import { useProjects } from "@/hooks/useProjects";
import { useAuthStore } from "@/stores/auth";
import { formatDate } from "@/lib/utils";
import { ProjectListSkeleton, StatCardSkeleton } from "@/components/common/Skeleton";

// ── Types ──────────────────────────────────────────────────────────────
interface Project {
  id: string;
  title: string;
  buyer: string | null;
  status: "draft" | "analyzing" | "ready" | "archived";
  submission_deadline: string | null;
  reference?: string | null;
}

// ── Status config avec couleurs design system ───────────────────────────
const STATUS_CONFIG = {
  draft:     { label: "Brouillon",  bg: "bg-slate-100",    text: "text-slate-600",  accent: "border-l-slate-400",  dot: "bg-slate-400"  },
  analyzing: { label: "En analyse", bg: "bg-primary-100",  text: "text-primary-800",accent: "border-l-primary-700",dot: "bg-primary-600" },
  ready:     { label: "Terminé",    bg: "bg-success-100",  text: "text-success-700",accent: "border-l-success-600", dot: "bg-success-600" },
  archived:  { label: "Archivé",    bg: "bg-slate-100",    text: "text-slate-400",  accent: "border-l-slate-300",  dot: "bg-slate-300"  },
};

// ── Stat Card Component ────────────────────────────────────────────────
function StatCard({
  icon,
  label,
  value,
  gradient,
  trend,
}: {
  icon: React.ReactNode;
  label: string;
  value: number | string;
  gradient: string;
  trend?: string;
}) {
  return (
    <div className={`rounded-2xl border p-5 shadow-card animate-slide-up ${gradient}`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-2">{label}</p>
          <p className="text-3xl font-extrabold text-slate-900">{value}</p>
          {trend && (
            <p className="text-xs text-slate-400 mt-1 flex items-center gap-1">
              <TrendingUp className="w-3 h-3 text-success-500" />
              {trend}
            </p>
          )}
        </div>
        <div className="p-2.5 rounded-xl bg-white/70 shadow-sm">{icon}</div>
      </div>
    </div>
  );
}

// ── Empty State ────────────────────────────────────────────────────────
function EmptyState() {
  return (
    <div className="empty-state animate-fade-in">
      <div className="w-16 h-16 rounded-2xl bg-primary-50 flex items-center justify-center mx-auto mb-4">
        <FolderOpen className="w-8 h-8 text-primary-400" />
      </div>
      <h3 className="text-slate-700 font-semibold text-lg">Aucun projet pour l&apos;instant</h3>
      <p className="text-slate-400 text-sm mt-1 max-w-xs mx-auto">
        Créez votre premier projet et importez vos documents DCE pour commencer l&apos;analyse IA.
      </p>
      <Link href="/projects/new" className="btn-primary-gradient inline-flex items-center gap-2 mt-6">
        <Plus className="w-4 h-4" /> Créer mon premier projet
      </Link>
    </div>
  );
}

// ── Main Page ──────────────────────────────────────────────────────────
export default function DashboardPage() {
  const { data, isLoading } = useProjects();
  const { user } = useAuthStore();
  const projects: Project[] = data?.items || [];

  const readyCount    = projects.filter(p => p.status === "ready").length;
  const analyzingCount = projects.filter(p => p.status === "analyzing").length;
  const draftCount    = projects.filter(p => p.status === "draft").length;

  // Salutation dynamique
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Bonjour" : hour < 18 ? "Bon après-midi" : "Bonsoir";
  const firstName = user?.full_name?.split(" ")[0] ?? "vous";

  // Date lisible
  const today = new Date().toLocaleDateString("fr-FR", {
    weekday: "long", day: "numeric", month: "long"
  });

  return (
    <div className="p-6 md:p-8 max-w-5xl mx-auto space-y-8">
      {/* ── Header ── */}
      <div className="flex items-start justify-between">
        <div className="animate-fade-in">
          <h1 className="text-2xl font-bold text-slate-900">
            {greeting}, {firstName} 👋
          </h1>
          <p className="text-slate-400 text-sm mt-0.5 capitalize">{today}</p>
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

      {/* ── Stat cards ── */}
      {isLoading ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map(i => <StatCardSkeleton key={i} />)}
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard
            icon={<FolderOpen className="w-5 h-5 text-primary-700" />}
            label="Projets"
            value={projects.length}
            gradient="bg-gradient-to-br from-primary-50 to-primary-100 border-primary-200"
          />
          <StatCard
            icon={<CheckCircle className="w-5 h-5 text-success-600" />}
            label="Terminés"
            value={readyCount}
            gradient="bg-gradient-to-br from-success-50 to-emerald-50 border-success-200"
          />
          <StatCard
            icon={<Clock className="w-5 h-5 text-warning-600" />}
            label="En analyse"
            value={analyzingCount}
            gradient="bg-gradient-to-br from-warning-50 to-amber-50 border-warning-200"
          />
          <StatCard
            icon={<FileText className="w-5 h-5 text-slate-500" />}
            label="Brouillons"
            value={draftCount}
            gradient="bg-gradient-to-br from-slate-50 to-slate-100 border-slate-200"
          />
        </div>
      )}

      {/* ── Getting started guide (shown when projects exist but none analyzed) ── */}
      {!isLoading && projects.length > 0 && readyCount === 0 && (
        <div className="rounded-xl border border-primary-200 bg-gradient-to-r from-primary-50 to-blue-50 p-5 animate-fade-in">
          <h3 className="font-semibold text-primary-800 text-sm mb-3">Premiers pas avec AO Copilot</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div className="flex items-start gap-3">
              <div className="w-7 h-7 rounded-full bg-primary-600 text-white flex items-center justify-center text-xs font-bold flex-shrink-0">1</div>
              <div>
                <p className="text-sm font-medium text-slate-700">Uploadez vos documents</p>
                <p className="text-xs text-slate-500">RC, CCAP, CCTP, AE, DPGF...</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-7 h-7 rounded-full bg-primary-600 text-white flex items-center justify-center text-xs font-bold flex-shrink-0">2</div>
              <div>
                <p className="text-sm font-medium text-slate-700">Lancez l&apos;analyse IA</p>
                <p className="text-xs text-slate-500">17 analyses automatiques en 5 min</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-7 h-7 rounded-full bg-primary-600 text-white flex items-center justify-center text-xs font-bold flex-shrink-0">3</div>
              <div>
                <p className="text-sm font-medium text-slate-700">Consultez les résultats</p>
                <p className="text-xs text-slate-500">Checklist, risques, scoring, export</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── Liste de projets ── */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-semibold text-slate-800">Vos projets</h2>
          {projects.length > 0 && (
            <span className="text-xs text-slate-400">{projects.length} projet{projects.length > 1 ? "s" : ""}</span>
          )}
        </div>

        {isLoading ? (
          <ProjectListSkeleton count={4} />
        ) : projects.length === 0 ? (
          <EmptyState />
        ) : (
          <div className="space-y-2">
            {projects.map((project, idx) => {
              const statusConf = STATUS_CONFIG[project.status] ?? STATUS_CONFIG.draft;
              const diff = project.submission_deadline
                ? new Date(project.submission_deadline).getTime() - Date.now()
                : 0;
              const isUrgent = project.submission_deadline
                ? diff > 0 && diff < 7 * 86400000
                : false;

              return (
                <Link
                  key={project.id}
                  href={`/projects/${project.id}`}
                  className={`card flex items-center justify-between p-4 pl-0 border-l-4
                    hover:shadow-card-hover transition-all duration-150 group
                    animate-slide-up ${statusConf.accent}`}
                  style={{ animationDelay: `${idx * 40}ms` }}
                >
                  <div className="flex items-center gap-4 pl-5 min-w-0">
                    {/* Status dot */}
                    <div className={`w-2 h-2 rounded-full flex-shrink-0 ${statusConf.dot}
                      ${project.status === "analyzing" ? "animate-pulse" : ""}`} />

                    <div className="min-w-0">
                      <p className="font-semibold text-slate-900 text-sm truncate group-hover:text-primary-800 transition-colors">
                        {project.title}
                      </p>
                      <p className="text-xs text-slate-400 mt-0.5 truncate">
                        {project.buyer ?? "Acheteur non renseigné"}
                        {project.reference && <span className="ml-2 text-slate-300">• {project.reference}</span>}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 pl-4 flex-shrink-0">
                    {project.submission_deadline && (
                      <div className={`hidden md:flex items-center gap-1.5 text-xs
                        ${isUrgent ? "text-danger-600 font-medium" : "text-slate-400"}`}>
                        <Calendar className="w-3.5 h-3.5" />
                        {formatDate(project.submission_deadline)}
                        {isUrgent && <span className="badge-manquant text-[10px] py-0 px-1.5">Urgent</span>}
                      </div>
                    )}

                    <span className={`badge text-xs ${statusConf.bg} ${statusConf.text}`}>
                      {statusConf.label}
                    </span>

                    <ChevronRight className="w-4 h-4 text-slate-300 group-hover:text-primary-500 group-hover:translate-x-0.5 transition-all" />
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
