"use client";

import { useState } from "react";
import {
  AlertTriangle,
  AlertOctagon,
  Info,
  ShieldAlert,
  FileX,
  HelpCircle,
  FileText,
  Copy,
  Check,
} from "lucide-react";
import { useQuestions } from "@/hooks/useAnalysis";
import { cn } from "@/lib/utils";
import AIDisclaimer from "@/components/ui/AIDisclaimer";

interface Props {
  projectId: string;
}

// ── Types ──────────────────────────────────────────────────────────────────

type Priority = "CRITIQUE" | "HAUTE" | "MOYENNE" | "BASSE";

interface Question {
  question: string;
  context: string;
  priority: Priority;
  related_doc: string;
  related_article: string;
  justification?: string;
}

interface QuestionsData {
  questions: Question[];
  resume: string;
  question_count: number;
  model_used: string;
}

// ── Priority helpers ──────────────────────────────────────────────────────

const PRIORITY_CONFIG: Record<
  Priority,
  {
    label: string;
    badgeCls: string;
    cardBorderCls: string;
    icon: React.ReactNode;
  }
> = {
  CRITIQUE: {
    label: "Critique",
    badgeCls: "bg-red-100 text-red-800 border border-red-200",
    cardBorderCls: "border-l-red-500",
    icon: <AlertOctagon className="w-4 h-4 text-red-600" />,
  },
  HAUTE: {
    label: "Haute",
    badgeCls: "bg-orange-100 text-orange-800 border border-orange-200",
    cardBorderCls: "border-l-orange-400",
    icon: <AlertTriangle className="w-4 h-4 text-orange-500" />,
  },
  MOYENNE: {
    label: "Moyenne",
    badgeCls: "bg-amber-100 text-amber-800 border border-amber-200",
    cardBorderCls: "border-l-amber-400",
    icon: <ShieldAlert className="w-4 h-4 text-amber-500" />,
  },
  BASSE: {
    label: "Basse",
    badgeCls: "bg-green-100 text-green-800 border border-green-200",
    cardBorderCls: "border-l-green-400",
    icon: <Info className="w-4 h-4 text-green-600" />,
  },
};

// ── Priority badge ────────────────────────────────────────────────────────

function PriorityBadge({ priority }: { priority: Priority }) {
  const cfg = PRIORITY_CONFIG[priority] ?? PRIORITY_CONFIG.MOYENNE;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold",
        cfg.badgeCls
      )}
      aria-label={`Priorite : ${cfg.label}`}
    >
      {cfg.icon}
      {cfg.label}
    </span>
  );
}

// ── Copy button ───────────────────────────────────────────────────────────

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback silently
    }
  };

  return (
    <button
      onClick={handleCopy}
      className={cn(
        "inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium transition-colors",
        copied
          ? "bg-green-100 text-green-700"
          : "bg-slate-100 text-slate-500 hover:bg-slate-200 hover:text-slate-700"
      )}
      title="Copier la question"
    >
      {copied ? (
        <>
          <Check className="w-3 h-3" />
          Copié
        </>
      ) : (
        <>
          <Copy className="w-3 h-3" />
          Copier
        </>
      )}
    </button>
  );
}

// ── Question card ─────────────────────────────────────────────────────────

function QuestionCard({
  question,
  index,
}: {
  question: Question;
  index: number;
}) {
  const cfg = PRIORITY_CONFIG[question.priority] ?? PRIORITY_CONFIG.MOYENNE;

  return (
    <div
      className={cn(
        "card border-l-4 p-4 space-y-2.5 animate-fade-in",
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
          <PriorityBadge priority={question.priority} />
          {/* Document & article chips */}
          {question.related_doc && (
            <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-slate-100 text-[10px] font-medium text-slate-500">
              <FileText className="w-3 h-3" />
              {question.related_doc}
            </span>
          )}
          {question.related_article && (
            <span className="inline-flex items-center px-1.5 py-0.5 rounded bg-slate-100 text-[10px] font-mono text-slate-600">
              {question.related_article}
            </span>
          )}
        </div>
        <div className="shrink-0">
          <CopyButton text={question.question} />
        </div>
      </div>

      {/* Question text */}
      <p className="text-sm font-medium text-slate-800 leading-snug">
        {question.question}
      </p>

      {/* Context explanation */}
      {question.context && (
        <p className="text-xs text-slate-500 leading-relaxed">
          {question.context}
        </p>
      )}

      {/* Justification — matching PDF/DOCX report */}
      {question.justification && (
        <div className="mt-1 pt-1.5 border-t border-slate-100">
          <p className="text-xs text-slate-500 leading-relaxed">
            <span className="font-semibold text-slate-600">Justification :</span>{" "}
            {question.justification}
          </p>
        </div>
      )}
    </div>
  );
}

// ── Filter pill ───────────────────────────────────────────────────────────

function FilterPill({
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

function QuestionsSkeleton() {
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
      </div>
      {/* Filter pills skeleton */}
      <div className="flex gap-2">
        {[1, 2, 3, 4, 5].map((i) => (
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

export function QuestionsTab({ projectId }: Props) {
  const { data, isLoading, isError } = useQuestions(projectId);
  const [activePriority, setActivePriority] = useState<string | null>(null);

  if (isLoading) return <QuestionsSkeleton />;

  if (isError) {
    return (
      <div className="card p-8 flex flex-col items-center gap-3 text-center animate-fade-in">
        <AlertTriangle className="w-10 h-10 text-amber-400" />
        <p className="text-slate-600 font-medium">
          Impossible de charger les questions à poser.
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

  const questionsData = data as QuestionsData;

  // Empty state: no questions generated
  if (!questionsData.questions || questionsData.questions.length === 0) {
    return (
      <div className="space-y-4 animate-fade-in">
        <div className="card p-6 flex items-center gap-5">
          <div className="w-12 h-12 rounded-xl bg-blue-50 flex items-center justify-center shrink-0">
            <HelpCircle className="w-6 h-6 text-blue-600" />
          </div>
          <div>
            <p className="font-semibold text-slate-800">
              Questions à poser à l&apos;acheteur
            </p>
            <p className="text-xs text-slate-400 mt-0.5">
              Analyse basée sur les documents du DCE
            </p>
          </div>
        </div>
        <div className="card p-10 flex flex-col items-center gap-4 text-center">
          <div className="w-14 h-14 rounded-2xl bg-green-50 flex items-center justify-center">
            <HelpCircle className="w-7 h-7 text-green-500" />
          </div>
          <div className="space-y-1">
            <p className="font-semibold text-slate-700">
              Aucune question identifiée
            </p>
            <p className="text-slate-400 text-sm max-w-sm">
              Le DCE analysé ne présente pas de zones d&apos;ombre nécessitant des
              clarifications auprès de l&apos;acheteur.
            </p>
          </div>
        </div>
        <AIDisclaimer compact />
      </div>
    );
  }

  const questions = questionsData.questions;

  // Priority counts
  const PRIORITIES: Priority[] = ["CRITIQUE", "HAUTE", "MOYENNE", "BASSE"];
  const countByPriority = (p: Priority) =>
    questions.filter((q) => q.priority === p).length;

  // Filter
  const filteredQuestions = activePriority
    ? questions.filter((q) => q.priority === activePriority)
    : questions;

  // Sort by priority: CRITIQUE -> HAUTE -> MOYENNE -> BASSE
  const sortedQuestions = [...filteredQuestions].sort(
    (a, b) => PRIORITIES.indexOf(a.priority) - PRIORITIES.indexOf(b.priority)
  );

  return (
    <div className="space-y-4 animate-fade-in">
      {/* ── Header card ── */}
      <div className="card p-5">
        <div className="flex flex-col sm:flex-row sm:items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-blue-50 flex items-center justify-center shrink-0">
            <HelpCircle className="w-6 h-6 text-blue-600" />
          </div>
          <div className="flex-1 space-y-1">
            <div className="flex items-center gap-3">
              <p className="font-semibold text-slate-800 text-base">
                Questions à poser à l&apos;acheteur
              </p>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-100 text-blue-800 border border-blue-200">
                {questionsData.question_count} question{questionsData.question_count > 1 ? "s" : ""}
              </span>
            </div>
          </div>
        </div>

        {/* Resume */}
        {questionsData.resume && (
          <div className="mt-4 pt-4 border-t border-slate-100">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">
              Synthèse
            </p>
            <p className="text-sm text-slate-700 leading-relaxed">
              {questionsData.resume}
            </p>
          </div>
        )}
      </div>

      {/* ── Priority filter pills ── */}
      <div className="flex flex-wrap gap-2">
        <FilterPill
          label="Toutes"
          count={questions.length}
          active={activePriority === null}
          onClick={() => setActivePriority(null)}
        />
        {PRIORITIES.map((p) => {
          const count = countByPriority(p);
          if (count === 0) return null;
          return (
            <FilterPill
              key={p}
              label={PRIORITY_CONFIG[p].label}
              count={count}
              active={activePriority === p}
              onClick={() =>
                setActivePriority(activePriority === p ? null : p)
              }
            />
          );
        })}
      </div>

      {/* ── Question cards ── */}
      <div className="space-y-3">
        {sortedQuestions.map((question, i) => (
          <QuestionCard key={i} question={question} index={i} />
        ))}
      </div>

      {/* ── Platform tip ── */}
      <div className="card p-3 bg-blue-50 border border-blue-100">
        <p className="text-xs text-blue-800 text-center leading-relaxed">
          <span className="font-semibold">Astuce :</span> Copiez les questions
          et posez-les sur la plateforme de dématérialisation (PLACE, AWS,
          eMarchés, Maximilien, etc.)
        </p>
      </div>

      {/* ── Footer disclaimer ── */}
      <AIDisclaimer />
    </div>
  );
}
