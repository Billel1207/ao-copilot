"use client";
import { Calendar, Clock, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";

// ── Types ────────────────────────────────────────────────────────────────────

export interface Deadline {
  id: string;
  project_id: string;
  deadline_type:
    | "remise_offres"
    | "visite_site"
    | "questions_acheteur"
    | "publication_resultats"
    | "autre";
  label: string;
  deadline_date: string;  // ISO 8601
  is_critical: boolean;
  citation: string | null;
  created_at: string;
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function formatDateFR(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString("fr-FR", {
      weekday: "long",
      day: "numeric",
      month: "long",
      year: "numeric",
    });
  } catch {
    return iso;
  }
}

function getDaysLeft(iso: string): number {
  const diff = new Date(iso).getTime() - Date.now();
  return Math.ceil(diff / (1000 * 60 * 60 * 24));
}

// ── Type badge ───────────────────────────────────────────────────────────────

const TYPE_CONFIGS: Record<
  Deadline["deadline_type"],
  { label: string; bgClass: string; textClass: string }
> = {
  remise_offres: {
    label: "Remise",
    bgClass: "bg-blue-100",
    textClass: "text-blue-800",
  },
  visite_site: {
    label: "Visite",
    bgClass: "bg-violet-100",
    textClass: "text-violet-800",
  },
  questions_acheteur: {
    label: "Q&A",
    bgClass: "bg-amber-100",
    textClass: "text-amber-800",
  },
  publication_resultats: {
    label: "Résultats",
    bgClass: "bg-emerald-100",
    textClass: "text-emerald-800",
  },
  autre: {
    label: "Autre",
    bgClass: "bg-slate-100",
    textClass: "text-slate-600",
  },
};

function TypeBadge({ type }: { type: Deadline["deadline_type"] }) {
  const cfg = TYPE_CONFIGS[type] ?? TYPE_CONFIGS.autre;
  return (
    <span
      className={cn(
        "inline-flex items-center text-[10px] font-bold px-2 py-0.5 rounded-full",
        cfg.bgClass,
        cfg.textClass
      )}
    >
      {cfg.label}
    </span>
  );
}

// ── Countdown badge ──────────────────────────────────────────────────────────

function CountdownBadge({ days }: { days: number }) {
  if (days < 0) {
    return (
      <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2.5 py-1 rounded-full bg-slate-100 text-slate-400">
        Passé
      </span>
    );
  }
  if (days === 0) {
    return (
      <span className="inline-flex items-center gap-1 text-[11px] font-bold px-2.5 py-1 rounded-full bg-red-100 text-red-700">
        <AlertTriangle className="w-3 h-3" />
        Aujourd&apos;hui
      </span>
    );
  }
  if (days <= 7) {
    return (
      <span className="inline-flex items-center gap-1 text-[11px] font-bold px-2.5 py-1 rounded-full bg-red-100 text-red-700">
        <AlertTriangle className="w-3 h-3" />
        J&#8209;{days}
      </span>
    );
  }
  if (days <= 14) {
    return (
      <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2.5 py-1 rounded-full bg-amber-100 text-amber-700">
        <Clock className="w-3 h-3" />
        J&#8209;{days}
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 text-[11px] font-medium px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700">
      <Calendar className="w-3 h-3" />
      J&#8209;{days}
    </span>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

interface DeadlineCardProps {
  deadline: Deadline;
}

export function DeadlineCard({ deadline }: DeadlineCardProps) {
  const days = getDaysLeft(deadline.deadline_date);
  const isUrgent = days >= 0 && days <= 7;
  const isWarning = days > 7 && days <= 14;
  const isPast = days < 0;

  return (
    <div
      className={cn(
        "card border-l-4 p-4 flex items-start justify-between gap-4 transition-all duration-150",
        deadline.is_critical && isUrgent
          ? "border-l-red-500 bg-red-50/40"
          : deadline.is_critical && isWarning
          ? "border-l-amber-500 bg-amber-50/30"
          : isPast
          ? "border-l-slate-200 bg-slate-50/30 opacity-70"
          : deadline.is_critical
          ? "border-l-blue-600 bg-blue-50/20"
          : "border-l-slate-200"
      )}
    >
      {/* Left: icon + content */}
      <div className="flex items-start gap-3 min-w-0">
        <div
          className={cn(
            "w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5",
            isUrgent
              ? "bg-red-100"
              : isWarning
              ? "bg-amber-100"
              : isPast
              ? "bg-slate-100"
              : "bg-primary-50"
          )}
        >
          <Calendar
            className={cn(
              "w-4 h-4",
              isUrgent
                ? "text-red-600"
                : isWarning
                ? "text-amber-600"
                : isPast
                ? "text-slate-400"
                : "text-primary-600"
            )}
          />
        </div>

        <div className="min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-0.5">
            <TypeBadge type={deadline.deadline_type} />
            {deadline.is_critical && !isPast && (
              <span className="text-[9px] font-bold uppercase tracking-wider text-red-500">
                Critique
              </span>
            )}
          </div>
          <p
            className={cn(
              "text-sm font-semibold truncate",
              isPast ? "text-slate-400 line-through" : "text-slate-800"
            )}
          >
            {deadline.label}
          </p>
          <p
            className={cn(
              "text-xs mt-0.5",
              isUrgent
                ? "text-red-600 font-medium"
                : isWarning
                ? "text-amber-700"
                : isPast
                ? "text-slate-400"
                : "text-slate-500"
            )}
          >
            {formatDateFR(deadline.deadline_date)}
          </p>
          {deadline.citation && (
            <p className="text-[10px] text-slate-400 mt-1 italic line-clamp-1">
              &laquo;&nbsp;{deadline.citation}&nbsp;&raquo;
            </p>
          )}
        </div>
      </div>

      {/* Right: countdown */}
      <div className="flex-shrink-0 mt-0.5">
        <CountdownBadge days={days} />
      </div>
    </div>
  );
}

// ── Deadlines list ────────────────────────────────────────────────────────────

interface DeadlineListProps {
  deadlines: Deadline[];
}

export function DeadlineList({ deadlines }: DeadlineListProps) {
  if (deadlines.length === 0) {
    return (
      <div className="empty-state animate-fade-in">
        <Calendar className="w-10 h-10 text-slate-200 mb-3" />
        <p className="font-semibold text-slate-700 mb-1">Aucune alerte date disponible</p>
        <p className="text-sm text-slate-400">
          Les dates clés seront extraites automatiquement lors de l&apos;analyse.
        </p>
      </div>
    );
  }

  const upcoming = deadlines.filter((d) => getDaysLeft(d.deadline_date) >= 0);
  const past = deadlines.filter((d) => getDaysLeft(d.deadline_date) < 0);

  return (
    <div className="space-y-3">
      {upcoming.map((d) => (
        <DeadlineCard key={d.id} deadline={d} />
      ))}
      {past.length > 0 && (
        <>
          <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider pt-1">
            Dates passées
          </p>
          {past.map((d) => (
            <DeadlineCard key={d.id} deadline={d} />
          ))}
        </>
      )}
    </div>
  );
}
