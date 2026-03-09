"use client";
import { Calendar, Clock, AlertTriangle, CheckCircle2, Loader2 } from "lucide-react";
import { useTimeline, useUpdateTimelineTask, useDeadlines } from "@/hooks/useAnalysis";
import { CardSkeleton } from "@/components/common/Skeleton";
import { DeadlineList } from "@/components/timeline/DeadlineCard";
import { cn } from "@/lib/utils";

interface Props { projectId: string; }

interface KeyDate {
  label: string;
  date: string | null;
  mandatory: boolean;
}

// ── Helpers ─────────────────────────────────────────────────────────────────
function formatDateFR(iso: string | null): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleDateString("fr-FR", {
      weekday: "short", day: "numeric", month: "long", year: "numeric",
    });
  } catch {
    return iso;
  }
}

function getDaysLeft(iso: string | null): number | null {
  if (!iso) return null;
  const diff = new Date(iso).getTime() - Date.now();
  return Math.ceil(diff / (1000 * 60 * 60 * 24));
}

function DaysLeftBadge({ days }: { days: number | null }) {
  if (days === null) return null;

  if (days < 0) {
    return (
      <span className="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-400">
        Passé
      </span>
    );
  }
  if (days === 0) {
    return (
      <span className="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full bg-red-100 text-red-700">
        <AlertTriangle className="w-2.5 h-2.5" /> Aujourd&apos;hui
      </span>
    );
  }
  if (days <= 7) {
    return (
      <span className="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full bg-red-100 text-red-700">
        <AlertTriangle className="w-2.5 h-2.5" /> J-{days}
      </span>
    );
  }
  if (days <= 30) {
    return (
      <span className="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-100 text-amber-700">
        J-{days}
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded-full bg-slate-100 text-slate-500">
      J-{days}
    </span>
  );
}

// ── Deadline Hero ────────────────────────────────────────────────────────────
function DeadlineHero({ deadline }: { deadline: string | null }) {
  const days = getDaysLeft(deadline);
  const isUrgent = days !== null && days >= 0 && days <= 7;
  const isPast = days !== null && days < 0;

  return (
    <div className={cn(
      "card border-l-4 p-5",
      isUrgent   ? "border-l-red-500 bg-red-50/50"    :
      isPast     ? "border-l-slate-300 bg-slate-50/50" :
                   "border-l-primary-500 bg-primary-50/30"
    )}>
      <div className="flex items-start justify-between flex-wrap gap-3">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Clock className={cn("w-4 h-4", isUrgent ? "text-red-500" : "text-primary-600")} />
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
              Date limite de remise des offres
            </p>
          </div>
          <p className={cn(
            "text-xl font-bold",
            isUrgent ? "text-red-700" : isPast ? "text-slate-400" : "text-slate-900"
          )}>
            {formatDateFR(deadline)}
          </p>
        </div>
        {days !== null && <DaysLeftBadge days={days} />}
      </div>

      {isUrgent && days !== null && days >= 0 && (
        <p className="text-xs text-red-600 mt-2 font-medium">
          ⚠ Attention : il ne reste que {days} jour{days > 1 ? "s" : ""} pour remettre votre offre.
        </p>
      )}
    </div>
  );
}

// ── Timeline item ────────────────────────────────────────────────────────────
function TimelineItem({
  item,
  isLast,
}: {
  item: KeyDate;
  isLast: boolean;
}) {
  const days = getDaysLeft(item.date);
  const isPast = days !== null && days < 0;
  const isUrgent = days !== null && days >= 0 && days <= 7;

  return (
    <div className="flex gap-4">
      {/* Line + dot */}
      <div className="flex flex-col items-center">
        <div className={cn(
          "w-3 h-3 rounded-full border-2 flex-shrink-0 mt-1",
          isPast     ? "bg-slate-200 border-slate-300"          :
          isUrgent   ? "bg-red-500 border-red-300 shadow-sm"   :
          item.mandatory ? "bg-primary-600 border-primary-300" :
                           "bg-slate-300 border-slate-200"
        )} />
        {!isLast && <div className="w-px flex-1 bg-slate-100 mt-1" />}
      </div>

      {/* Content */}
      <div className={cn("pb-5 flex-1", isLast && "pb-0")}>
        <div className="flex items-start justify-between gap-2 flex-wrap">
          <div>
            <p className={cn(
              "text-sm font-medium",
              isPast ? "text-slate-400 line-through" : "text-slate-800"
            )}>
              {item.label}
            </p>
            <p className={cn(
              "text-xs mt-0.5",
              isUrgent ? "text-red-600 font-semibold" :
              isPast   ? "text-slate-400"              :
                         "text-slate-500"
            )}>
              {formatDateFR(item.date)}
            </p>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            {item.mandatory && (
              <span className="text-[10px] font-bold bg-primary-100 text-primary-700 px-1.5 py-0.5 rounded">
                Obligatoire
              </span>
            )}
            <DaysLeftBadge days={days} />
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Main Component ───────────────────────────────────────────────────────────
export function TimelineTab({ projectId }: Props) {
  const { data, isLoading, error } = useTimeline(projectId, true);
  const updateTask = useUpdateTimelineTask(projectId);
  const { data: deadlines = [], isLoading: deadlinesLoading } = useDeadlines(projectId, true);

  if (isLoading) {
    return (
      <div className="space-y-3 max-w-2xl">
        {[1, 2, 3].map(i => <CardSkeleton key={i} />)}
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="empty-state animate-fade-in">
        <Calendar className="w-10 h-10 text-slate-200 mb-3" />
        <p className="font-semibold text-slate-700 mb-1">Calendrier non disponible</p>
        <p className="text-sm text-slate-400">
          Lancez l&apos;analyse pour extraire automatiquement toutes les dates du DCE.
        </p>
      </div>
    );
  }

  const {
    submission_deadline,
    execution_start,
    execution_duration_months,
    site_visit_date,
    questions_deadline,
    key_dates = [],
    suggested_tasks = [],
  } = data;

  return (
    <div className="max-w-2xl space-y-6 animate-fade-in">

      {/* ── Deadline hero ── */}
      <DeadlineHero deadline={submission_deadline} />

      {/* ── Alertes dates clés structurées (ProjectDeadline) ── */}
      {(deadlines.length > 0 || deadlinesLoading) && (
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-slate-700 mb-4 flex items-center gap-2">
            <Clock className="w-4 h-4 text-primary-600" />
            Alertes dates clés
          </h3>
          {deadlinesLoading ? (
            <CardSkeleton />
          ) : (
            <DeadlineList deadlines={deadlines} />
          )}
        </div>
      )}

      {/* ── Key dates timeline ── */}
      {key_dates.length > 0 && (
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-slate-700 mb-4 flex items-center gap-2">
            <Calendar className="w-4 h-4 text-primary-600" />
            Dates clés du marché
          </h3>

          <div>
            {key_dates.map((item: KeyDate, i: number) => (
              <TimelineItem key={i} item={item} isLast={i === key_dates.length - 1} />
            ))}
          </div>
        </div>
      )}

      {/* ── Execution info ── */}
      {(execution_start || execution_duration_months || site_visit_date || questions_deadline) && (
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-slate-700 mb-4">Informations complémentaires</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {execution_start && (
              <InfoBox label="Début d'exécution" value={formatDateFR(execution_start)} />
            )}
            {execution_duration_months && (
              <InfoBox label="Durée du marché" value={`${execution_duration_months} mois`} />
            )}
            {site_visit_date && (
              <InfoBox label="Visite de site" value={formatDateFR(site_visit_date)} badge={<DaysLeftBadge days={getDaysLeft(site_visit_date)} />} />
            )}
            {questions_deadline && (
              <InfoBox label="Limite questions" value={formatDateFR(questions_deadline)} badge={<DaysLeftBadge days={getDaysLeft(questions_deadline)} />} />
            )}
          </div>
        </div>
      )}

      {/* ── Suggested tasks checklist ── */}
      {suggested_tasks && suggested_tasks.length > 0 && (
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-success-600" />
            Tâches à accomplir
          </h3>
          <div className="space-y-2">
            {suggested_tasks.map((task: { label: string; done?: boolean; priority?: string }, i: number) => (
              <label
                key={i}
                className={cn(
                  "flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-all duration-150",
                  task.done
                    ? "bg-success-50/40 border-success-100 opacity-60"
                    : "bg-white border-slate-100 hover:border-primary-200 hover:bg-primary-50/30"
                )}
              >
                <input
                  type="checkbox"
                  checked={task.done || false}
                  onChange={(e) => updateTask.mutate({ taskIndex: i, done: e.target.checked })}
                  disabled={updateTask.isPending}
                  className="w-4 h-4 accent-primary-600 flex-shrink-0 cursor-pointer"
                />
                <span className={cn(
                  "text-sm flex-1",
                  task.done ? "line-through text-slate-400" : "text-slate-700"
                )}>
                  {task.label}
                </span>
                {task.priority && (
                  <span className={cn(
                    "text-[10px] font-bold px-1.5 py-0.5 rounded flex-shrink-0",
                    task.priority === "P0" ? "bg-red-100 text-red-700" :
                    task.priority === "P1" ? "bg-amber-100 text-amber-700" :
                                             "bg-slate-100 text-slate-500"
                  )}>
                    {task.priority}
                  </span>
                )}
                {updateTask.isPending && (
                  <Loader2 className="w-3 h-3 animate-spin text-slate-300 flex-shrink-0" />
                )}
              </label>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Info box helper ──────────────────────────────────────────────────────────
function InfoBox({ label, value, badge }: { label: string; value: string; badge?: React.ReactNode }) {
  return (
    <div className="bg-slate-50 rounded-lg p-3 border border-slate-100">
      <p className="text-[10px] text-slate-400 font-semibold uppercase tracking-wide mb-0.5">{label}</p>
      <div className="flex items-center justify-between gap-2">
        <p className="text-sm font-semibold text-slate-800">{value}</p>
        {badge}
      </div>
    </div>
  );
}
