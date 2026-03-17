"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import {
  Plus, Search, FolderOpen, Clock, CheckCircle2,
  Loader2, AlertCircle, ChevronRight, FileText, Calendar,
  ArrowUpDown
} from "lucide-react";
import { useProjects } from "@/hooks/useProjects";
import { formatDate, cn } from "@/lib/utils";
import { ProjectListSkeleton } from "@/components/common/Skeleton";

// ── Types & config ────────────────────────────────────────────────────────

interface Project {
  id: string;
  title: string;
  buyer: string | null;
  status: "draft" | "processing" | "analyzing" | "ready" | "archived" | "error";
  submission_deadline: string | null;
  reference?: string | null;
}

const STATUS_CONFIG: Record<string, { label: string; badge: string; accent: string; dot: string }> = {
  draft:     { label: "Brouillon",   badge: "bg-slate-100 text-slate-600",    accent: "border-l-slate-300",   dot: "bg-slate-400"  },
  processing:{ label: "Extraction",  badge: "bg-blue-100 text-blue-700",      accent: "border-l-blue-400",    dot: "bg-blue-500"   },
  analyzing: { label: "En analyse",  badge: "bg-primary-100 text-primary-800",accent: "border-l-primary-600", dot: "bg-primary-600"},
  ready:     { label: "Terminé",     badge: "bg-success-100 text-success-700",accent: "border-l-success-500", dot: "bg-success-600"},
  error:     { label: "Erreur",      badge: "bg-danger-100 text-danger-700",  accent: "border-l-danger-500",  dot: "bg-danger-600" },
  archived:  { label: "Archivé",     badge: "bg-slate-100 text-slate-400",   accent: "border-l-slate-200",   dot: "bg-slate-300"  },
};

const STATUS_FILTERS = [
  { value: "",          label: "Tous" },
  { value: "ready",     label: "Terminés" },
  { value: "analyzing", label: "En analyse" },
  { value: "draft",     label: "Brouillons" },
  { value: "archived",  label: "Archivés" },
];

// ── Project Card ──────────────────────────────────────────────────────────

function ProjectCard({ project }: { project: Project }) {
  const cfg = STATUS_CONFIG[project.status] ?? STATUS_CONFIG.draft;
  const deadline = project.submission_deadline ? new Date(project.submission_deadline) : null;
  const daysLeft = deadline ? Math.ceil((deadline.getTime() - Date.now()) / (1000 * 60 * 60 * 24)) : null;
  const isUrgent = daysLeft !== null && daysLeft >= 0 && daysLeft <= 7;

  return (
    <Link href={`/projects/${project.id}`} className="block group">
      <div className={cn(
        "card p-5 border-l-4 transition-all duration-150 group-hover:shadow-card-hover group-hover:-translate-y-px",
        cfg.accent
      )}>
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            {/* Titre + badge statut */}
            <div className="flex items-center gap-2 flex-wrap mb-1">
              <h3 className="font-semibold text-slate-900 text-sm group-hover:text-primary-800 transition-colors truncate max-w-sm">
                {project.title}
              </h3>
              <span className={`inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full flex-shrink-0 ${cfg.badge}`}>
                <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
                {cfg.label}
              </span>
            </div>

            {/* Meta */}
            <div className="flex items-center gap-3 text-xs text-slate-400 flex-wrap">
              {project.buyer && (
                <span className="flex items-center gap-1">
                  <FileText className="w-3 h-3" /> {project.buyer}
                </span>
              )}
              {project.reference && (
                <span className="font-mono bg-slate-50 px-1.5 py-0.5 rounded text-slate-500">
                  {project.reference}
                </span>
              )}
              {deadline && (
                <span className={cn(
                  "flex items-center gap-1",
                  isUrgent ? "text-danger-600 font-semibold" : "text-slate-400"
                )}>
                  <Calendar className="w-3 h-3" />
                  {isUrgent ? `⚠ ${daysLeft}j restants` : formatDate(project.submission_deadline!)}
                </span>
              )}
            </div>
          </div>

          <ChevronRight className="w-4 h-4 text-slate-300 group-hover:text-primary-400 flex-shrink-0 mt-0.5 transition-colors" />
        </div>
      </div>
    </Link>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────

type SortKey = "deadline" | "title" | "status" | "";

const SORT_OPTIONS: { value: SortKey; label: string }[] = [
  { value: "",         label: "Par défaut" },
  { value: "deadline", label: "Date limite ↑" },
  { value: "title",    label: "Nom A→Z" },
  { value: "status",   label: "Statut" },
];

export default function ProjectsPage() {
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [sortBy, setSortBy] = useState<SortKey>("");

  // Debounce 300ms — envoie la recherche au serveur seulement après pause
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search.trim());
    }, 300);
    return () => clearTimeout(timer);
  }, [search]);

  const { data, isLoading } = useProjects({
    status: statusFilter || undefined,
    q: debouncedSearch || undefined,
  });

  const projects: Project[] = data?.items ?? [];

  // Sort projects client-side based on selected sort key
  const STATUS_ORDER: Record<string, number> = { analyzing: 0, draft: 1, processing: 2, ready: 3, error: 4, archived: 5 };
  const filtered = [...projects].sort((a, b) => {
    if (sortBy === "deadline") {
      const da = a.submission_deadline ? new Date(a.submission_deadline).getTime() : Infinity;
      const db = b.submission_deadline ? new Date(b.submission_deadline).getTime() : Infinity;
      return da - db;
    }
    if (sortBy === "title") return (a.title || "").localeCompare(b.title || "", "fr");
    if (sortBy === "status") return (STATUS_ORDER[a.status] ?? 9) - (STATUS_ORDER[b.status] ?? 9);
    return 0;
  });

  return (
    <div className="p-6 md:p-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-7 flex-wrap gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Projets AO</h1>
          <p className="text-slate-400 text-sm mt-0.5">
            {projects.length} projet{projects.length > 1 ? "s" : ""} au total
          </p>
        </div>
        <Link href="/projects/new" className="btn-primary-gradient flex items-center gap-2">
          <Plus className="w-4 h-4" /> Nouveau projet
        </Link>
      </div>

      {/* Filtres */}
      <div className="flex flex-col sm:flex-row gap-3 mb-6">
        {/* Recherche */}
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Rechercher par titre, acheteur, référence…"
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="input-field pl-9"
          />
        </div>

        {/* Filtre statut */}
        <div className="flex items-center gap-1.5 flex-wrap">
          {STATUS_FILTERS.map(f => (
            <button
              key={f.value}
              onClick={() => setStatusFilter(f.value)}
              className={cn(
                "px-3 py-2 text-xs font-medium rounded-xl transition-all duration-150",
                statusFilter === f.value
                  ? "bg-primary-800 text-white shadow-sm"
                  : "bg-white border border-slate-200 text-slate-600 hover:border-slate-300"
              )}
            >
              {f.label}
            </button>
          ))}
        </div>

        {/* Tri */}
        <div className="flex items-center gap-1.5">
          <ArrowUpDown className="w-3.5 h-3.5 text-slate-400" />
          <select
            value={sortBy}
            onChange={e => setSortBy(e.target.value as SortKey)}
            className="text-xs border border-slate-200 rounded-xl px-3 py-2 bg-white text-slate-600 focus:ring-1 focus:ring-primary-300 focus:border-primary-300 outline-none"
          >
            {SORT_OPTIONS.map(o => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Liste */}
      {isLoading ? (
        <ProjectListSkeleton count={5} />
      ) : filtered.length === 0 ? (
        <div className="empty-state">
          <div className="w-14 h-14 rounded-2xl bg-primary-50 flex items-center justify-center mx-auto mb-4">
            <FolderOpen className="w-7 h-7 text-primary-300" />
          </div>
          <p className="font-semibold text-slate-700 mb-1">
            {search || statusFilter ? "Aucun projet correspond à vos filtres" : "Aucun projet créé"}
          </p>
          <p className="text-sm text-slate-400 mb-5">
            {search || statusFilter
              ? "Essayez de modifier vos critères de recherche"
              : "Créez votre premier projet et importez vos PDFs DCE"}
          </p>
          {!search && !statusFilter && (
            <Link href="/projects/new" className="btn-primary-gradient inline-flex items-center gap-2">
              <Plus className="w-4 h-4" /> Créer un projet
            </Link>
          )}
        </div>
      ) : (
        <div className="space-y-2">
          {filtered.map(p => <ProjectCard key={p.id} project={p} />)}
        </div>
      )}
    </div>
  );
}
