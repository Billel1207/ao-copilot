"use client";

export const dynamic = "force-dynamic";
import { useState, useEffect, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft, Upload, Loader2, Play, FileText,
  CheckSquare, Target, Download, Clock, CheckCircle2,
  AlertCircle, Zap, RefreshCw, MessageSquare, Calendar,
  TrendingUp, Eye, X, ShieldAlert, Trophy, ThumbsDown, Ban, Pencil,
  ScrollText, FileCheck, GitCompareArrows, HelpCircle, BarChart3, DollarSign,
  Wrench, Wallet, Users,
} from "lucide-react";
import { toast } from "sonner";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useProject } from "@/hooks/useProjects";
import { useDocuments } from "@/hooks/useDocuments";
import { useSummary, useTriggerAnalysis } from "@/hooks/useAnalysis";
import { documentsApi, projectsApi } from "@/lib/api";
import { SummaryTab }   from "@/components/summary/SummaryTab";
import { ChecklistTab } from "@/components/checklist/ChecklistTab";
import { CriteriaTab }  from "@/components/criteria/CriteriaTab";
import { ExportTab }    from "@/components/export/ExportTab";
import { ChatTab }      from "@/components/chat/ChatTab";
import { TimelineTab }  from "@/components/timeline/TimelineTab";
import { GoNoGoCard }   from "@/components/gonogo/GoNoGoCard";
import { CcapRiskTab }  from "@/components/analysis/CcapRiskTab";
import { RcAnalysisTab }  from "@/components/analysis/RcAnalysisTab";
import { AeAnalysisTab }  from "@/components/analysis/AeAnalysisTab";
import { DcCheckTab }      from "@/components/analysis/DcCheckTab";
import { ConflictsTab }    from "@/components/analysis/ConflictsTab";
import { QuestionsTab }    from "@/components/analysis/QuestionsTab";
import { ScoringSimulatorTab } from "@/components/analysis/ScoringSimulatorTab";
import { DpgfPricingTab }  from "@/components/analysis/DpgfPricingTab";
import CctpAnalysisTab from "@/components/analysis/CctpAnalysisTab";
import CashFlowTab from "@/components/analysis/CashFlowTab";
import SubcontractingTab from "@/components/analysis/SubcontractingTab";
import OcrQualityBanner from "@/components/ui/OcrQualityBanner";
import { ProgressAnalysis } from "@/components/ui/ProgressAnalysis";
import { ProjectDetailSkeleton } from "@/components/common/Skeleton";
import { cn, formatDate } from "@/lib/utils";

// ── Tab config (grouped into 4 categories) ──────────────────────────────
const TAB_GROUPS = [
  {
    label: "Synthèse",
    tabs: [
      { key: "documents",  label: "Documents",    icon: FileText          },
      { key: "summary",    label: "Résumé",       icon: FileText          },
      { key: "checklist",  label: "Checklist",    icon: CheckSquare       },
      { key: "criteria",   label: "Critères",     icon: Target            },
    ],
  },
  {
    label: "Analyse pièces",
    tabs: [
      { key: "ccap",       label: "CCAP",         icon: ShieldAlert       },
      { key: "rc",         label: "RC",           icon: ScrollText        },
      { key: "ae",         label: "Acte Eng.",    icon: FileCheck         },
      { key: "cctp",       label: "CCTP",         icon: Wrench            },
      { key: "dc",         label: "Admin.",       icon: FileCheck         },
      { key: "conflicts",  label: "Conflits",     icon: GitCompareArrows  },
    ],
  },
  {
    label: "Stratégie",
    tabs: [
      { key: "questions",       label: "Questions",       icon: HelpCircle        },
      { key: "scoring",         label: "Scoring",         icon: BarChart3         },
      { key: "pricing",         label: "Pricing",         icon: DollarSign        },
      { key: "cashflow",        label: "Trésorerie",      icon: Wallet            },
      { key: "subcontracting",  label: "Sous-traitance",  icon: Users             },
    ],
  },
  {
    label: "Outils",
    tabs: [
      { key: "timeline",   label: "Calendrier",   icon: Calendar          },
      { key: "chat",       label: "Chat DCE",     icon: MessageSquare     },
      { key: "export",     label: "Export",       icon: Download          },
    ],
  },
];

// Flat list for filtering/rendering
const TABS = TAB_GROUPS.flatMap(g => g.tabs);

// ── Status badge ─────────────────────────────────────────────────────────
const STATUS_CONFIG: Record<string, { label: string; color: string; icon: React.ReactNode }> = {
  draft:     { label: "Brouillon",  color: "bg-slate-100 text-slate-600",     icon: <FileText className="w-3 h-3" /> },
  processing:{ label: "Extraction", color: "bg-blue-100 text-blue-700",       icon: <Loader2 className="w-3 h-3 animate-spin" /> },
  analyzing: { label: "Analyse IA", color: "bg-amber-100 text-amber-700",     icon: <Zap className="w-3 h-3 animate-pulse" /> },
  ready:     { label: "Prêt",       color: "bg-success-100 text-success-700", icon: <CheckCircle2 className="w-3 h-3" /> },
  error:     { label: "Erreur",     color: "bg-danger-100 text-danger-700",   icon: <AlertCircle className="w-3 h-3" /> },
  archived:  { label: "Archivé",    color: "bg-slate-100 text-slate-500",     icon: <FileText className="w-3 h-3" /> },
};

function StatusBadge({ status }: { status: string }) {
  const cfg = STATUS_CONFIG[status] ?? STATUS_CONFIG.draft;
  return (
    <span className={`inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full ${cfg.color}`}>
      {cfg.icon}
      {cfg.label}
    </span>
  );
}

// ── Doc type colors ──────────────────────────────────────────────────────
const DOC_TYPE_COLORS: Record<string, string> = {
  RC:    "bg-primary-100 text-primary-800",
  CCTP:  "bg-blue-100 text-blue-800",
  CCAP:  "bg-success-100 text-success-700",
  DPGF:  "bg-warning-100 text-warning-700",
  BPU:   "bg-purple-100 text-purple-700",
  AE:    "bg-pink-100 text-pink-700",
  ATTRI: "bg-indigo-100 text-indigo-700",
  AUTRES:"bg-slate-100 text-slate-600",
};

const DOC_STATUS: Record<string, { label: string; border: string }> = {
  done:       { label: "Extrait",    border: "border-l-4 border-l-success-500" },
  processing: { label: "En cours…",  border: "border-l-4 border-l-primary-400" },
  error:      { label: "Erreur",     border: "border-l-4 border-l-danger-500"  },
  pending:    { label: "En attente", border: "border-l-4 border-l-slate-200"   },
};

// ── PDF Viewer Modal ──────────────────────────────────────────────────────
function PdfViewerModal({
  projectId, docId, docName, onClose,
}: {
  projectId: string; docId: string; docName: string; onClose: () => void;
}) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["signed-url", docId],
    queryFn: () => documentsApi.getSignedUrl(projectId, docId).then(r => r.data),
    staleTime: 10 * 60 * 1000, // 10 min (URL valide 15 min)
  });

  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-50 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-white border-b border-slate-200 flex-shrink-0 shadow-sm">
        <div className="flex items-center gap-2 min-w-0">
          <FileText className="w-4 h-4 text-primary-600 flex-shrink-0" />
          <span className="text-sm font-semibold text-slate-800 truncate max-w-lg">{docName}</span>
        </div>
        <button
          onClick={onClose}
          className="ml-4 p-1.5 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-700 transition flex-shrink-0"
          title="Fermer (Échap)"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Viewer */}
      <div className="flex-1 relative bg-slate-700">
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center">
            <Loader2 className="w-8 h-8 text-white animate-spin" />
          </div>
        )}
        {isError && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 text-white">
            <AlertCircle className="w-10 h-10 text-slate-300" />
            <p className="text-sm text-slate-300">Impossible de charger le document.</p>
            <button onClick={onClose} className="text-xs underline text-slate-400 hover:text-white">Fermer</button>
          </div>
        )}
        {data?.url && (
          <iframe
            src={data.url}
            className="w-full h-full border-0"
            title={docName}
          />
        )}
      </div>
    </div>
  );
}

// ── Win/Loss Result Section ──────────────────────────────────────────────
const RESULT_CONFIG = {
  won:    { label: "Remporté",    color: "bg-success-100 text-success-700 border-success-200",   icon: Trophy,     badgeColor: "bg-success-500"   },
  lost:   { label: "Perdu",       color: "bg-danger-100 text-danger-700 border-danger-200",       icon: ThumbsDown, badgeColor: "bg-danger-500"    },
  no_bid: { label: "Non répondu", color: "bg-slate-100 text-slate-600 border-slate-200",          icon: Ban,        badgeColor: "bg-slate-400"     },
};

type ProjectResult = "won" | "lost" | "no_bid";

interface ResultModalProps {
  initialResult: ProjectResult;
  initialAmount?: number | null;
  initialNotes?: string | null;
  onClose: () => void;
  onSave: (data: { result: ProjectResult; result_amount_eur?: number | null; result_notes?: string | null }) => void;
  isSaving: boolean;
}

function ResultModal({ initialResult, initialAmount, initialNotes, onClose, onSave, isSaving }: ResultModalProps) {
  const [result, setResult] = useState<ProjectResult>(initialResult);
  const [amount, setAmount] = useState<string>(initialAmount ? String(initialAmount) : "");
  const [notes, setNotes] = useState<string>(initialNotes || "");

  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  const handleSave = () => {
    onSave({
      result,
      result_amount_eur: amount ? parseFloat(amount) : null,
      result_notes: notes || null,
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" onClick={onClose}>
      <div
        className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 animate-fade-in"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-base font-bold text-slate-900">Résultat de l&apos;appel d&apos;offres</h3>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Result choice */}
        <div className="grid grid-cols-3 gap-2 mb-5">
          {(["won", "lost", "no_bid"] as ProjectResult[]).map(r => {
            const cfg = RESULT_CONFIG[r];
            const Icon = cfg.icon;
            return (
              <button
                key={r}
                onClick={() => setResult(r)}
                className={cn(
                  "flex flex-col items-center gap-1.5 p-3 rounded-xl border-2 text-sm font-semibold transition-all",
                  result === r ? cfg.color + " border-current shadow-sm" : "border-slate-200 text-slate-500 hover:border-slate-300"
                )}
              >
                <Icon className="w-5 h-5" />
                {cfg.label}
              </button>
            );
          })}
        </div>

        {/* Amount — only for "won" */}
        {result === "won" && (
          <div className="mb-4">
            <label className="block text-sm font-medium text-slate-700 mb-1.5">
              Montant du marché (€) <span className="text-slate-400 font-normal">facultatif</span>
            </label>
            <input
              type="number"
              min="0"
              step="0.01"
              className="input-field"
              placeholder="150000"
              value={amount}
              onChange={e => setAmount(e.target.value)}
            />
          </div>
        )}

        {/* Notes */}
        <div className="mb-5">
          <label className="block text-sm font-medium text-slate-700 mb-1.5">
            Notes <span className="text-slate-400 font-normal">facultatif</span>
          </label>
          <textarea
            className="input-field resize-none"
            rows={3}
            maxLength={500}
            placeholder="Commentaires sur le résultat, raison de la perte…"
            value={notes}
            onChange={e => setNotes(e.target.value)}
          />
          <p className="text-xs text-slate-400 text-right mt-0.5">{notes.length}/500</p>
        </div>

        <div className="flex gap-3">
          <button onClick={onClose} className="btn-secondary flex-1">Annuler</button>
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="btn-primary-gradient flex-1 flex items-center justify-center gap-2"
          >
            {isSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
            Enregistrer
          </button>
        </div>
      </div>
    </div>
  );
}

interface WinLossSectionProps {
  project: {
    id: string;
    result?: string | null;
    result_amount_eur?: number | null;
    result_date?: string | null;
    result_notes?: string | null;
  };
}

function WinLossSection({ project }: WinLossSectionProps) {
  const queryClient = useQueryClient();
  const [showModal, setShowModal] = useState(false);

  const mutation = useMutation({
    mutationFn: (data: { result: ProjectResult; result_amount_eur?: number | null; result_notes?: string | null }) =>
      projectsApi.updateResult(project.id, data),
    onSuccess: () => {
      toast.success("Résultat enregistré");
      queryClient.invalidateQueries({ queryKey: ["project", project.id] });
      setShowModal(false);
    },
    onError: () => {
      toast.error("Erreur lors de l'enregistrement");
    },
  });

  const openModal = useCallback(() => setShowModal(true), []);
  const closeModal = useCallback(() => setShowModal(false), []);

  const hasResult = !!project.result && project.result in RESULT_CONFIG;
  const resultCfg = hasResult ? RESULT_CONFIG[project.result as ProjectResult] : null;
  const ResultIcon = resultCfg?.icon;

  return (
    <>
      {showModal && (
        <ResultModal
          initialResult={(project.result as ProjectResult) || "won"}
          initialAmount={project.result_amount_eur}
          initialNotes={project.result_notes}
          onClose={closeModal}
          onSave={mutation.mutate}
          isSaving={mutation.isPending}
        />
      )}

      <div className="px-6 md:px-8 pt-5 pb-0">
        <div className="card p-5">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Trophy className="w-4 h-4 text-primary-600" />
              <h2 className="text-sm font-semibold text-slate-700">Résultat de l&apos;appel d&apos;offres</h2>
            </div>
            {hasResult && (
              <button
                onClick={openModal}
                className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-primary-600 transition-colors"
              >
                <Pencil className="w-3 h-3" />
                Modifier
              </button>
            )}
          </div>

          {hasResult && resultCfg && ResultIcon ? (
            <div className="flex items-center gap-4 flex-wrap">
              <span className={cn(
                "inline-flex items-center gap-2 text-sm font-semibold px-3 py-1.5 rounded-full border",
                resultCfg.color
              )}>
                <ResultIcon className="w-4 h-4" />
                {resultCfg.label}
              </span>

              {project.result_amount_eur && (
                <span className="text-sm font-bold text-slate-800">
                  {new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(project.result_amount_eur)}
                </span>
              )}

              {project.result_date && (
                <span className="text-xs text-slate-400">
                  {formatDate(project.result_date)}
                </span>
              )}

              {project.result_notes && (
                <p className="w-full text-xs text-slate-500 mt-1 bg-slate-50 rounded-lg px-3 py-2 border border-slate-100">
                  {project.result_notes}
                </p>
              )}
            </div>
          ) : (
            <div>
              <p className="text-xs text-slate-400 mb-3">Enregistrez le résultat de cet appel d&apos;offres</p>
              <div className="flex gap-2 flex-wrap">
                {(["won", "lost", "no_bid"] as ProjectResult[]).map(r => {
                  const cfg = RESULT_CONFIG[r];
                  const Icon = cfg.icon;
                  return (
                    <button
                      key={r}
                      onClick={() => {
                        mutation.mutate({ result: r });
                      }}
                      disabled={mutation.isPending}
                      className={cn(
                        "flex items-center gap-1.5 text-sm font-semibold px-4 py-2 rounded-xl border-2 transition-all",
                        "border-slate-200 text-slate-600 hover:border-current",
                        r === "won"    ? "hover:text-success-700 hover:border-success-400 hover:bg-success-50" :
                        r === "lost"   ? "hover:text-danger-700 hover:border-danger-400 hover:bg-danger-50" :
                                          "hover:text-slate-700 hover:border-slate-400 hover:bg-slate-50"
                      )}
                    >
                      {mutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Icon className="w-4 h-4" />}
                      {cfg.label}
                    </button>
                  );
                })}
                <button
                  onClick={openModal}
                  className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-primary-600 px-3 py-2 rounded-xl border border-dashed border-slate-200 hover:border-primary-300 transition-all"
                >
                  <Pencil className="w-3 h-3" />
                  Avec notes
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}


// ── Main Page ─────────────────────────────────────────────────────────────
export default function ProjectPage() {
  const params = useParams();
  const projectId = params.id as string;
  const [activeTab, setActiveTab] = useState("documents");
  const [viewingDoc, setViewingDoc] = useState<{ id: string; name: string } | null>(null);

  const { data: project, isLoading: projectLoading } = useProject(projectId);
  const { data: documents } = useDocuments(projectId);
  const { data: summary } = useSummary(projectId, project?.status === "ready");
  const triggerAnalysis = useTriggerAnalysis(projectId);

  const handleAnalyze = async () => {
    try {
      await triggerAnalysis.mutateAsync();
      toast.success("Analyse lancée — résultats disponibles dans 2–5 minutes");
    } catch {
      toast.error("Erreur lors du lancement de l'analyse");
    }
  };

  if (projectLoading) return <ProjectDetailSkeleton />;
  if (!project) return (
    <div className="flex flex-col items-center justify-center h-full text-slate-400 gap-3">
      <AlertCircle className="w-10 h-10 text-slate-200" />
      <p>Projet introuvable</p>
      <Link href="/dashboard" className="btn-secondary text-sm">Retour au tableau de bord</Link>
    </div>
  );

  const canAnalyze = (documents?.length || 0) > 0 && !["analyzing", "processing"].includes(project.status);
  const isReady = project.status === "ready";

  // Urgence délai : moins de 7 jours
  const deadline = project.submission_deadline ? new Date(project.submission_deadline) : null;
  const daysLeft = deadline ? Math.ceil((deadline.getTime() - Date.now()) / (1000 * 60 * 60 * 24)) : null;
  const isUrgent = daysLeft !== null && daysLeft >= 0 && daysLeft <= 7;

  // Tabs visibles selon statut
  const visibleTabs = TABS.filter(t => {
    if (["timeline", "chat", "checklist", "criteria", "summary", "export", "ccap",
         "rc", "ae", "dc", "conflicts", "questions", "scoring", "pricing", "cctp", "cashflow"].includes(t.key)) {
      return isReady;
    }
    return true;
  });

  return (
    <div className="flex flex-col min-h-full">
      {viewingDoc && (
        <PdfViewerModal
          projectId={projectId}
          docId={viewingDoc.id}
          docName={viewingDoc.name}
          onClose={() => setViewingDoc(null)}
        />
      )}

      {/* ── Header ── */}
      <div className="px-6 md:px-8 py-5 border-b border-slate-200 bg-white sticky top-0 z-20">
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-1.5 text-slate-400 text-xs hover:text-primary-700 transition-colors mb-3"
        >
          <ArrowLeft className="w-3 h-3" /> Tableau de bord
        </Link>

        <div className="flex items-start justify-between gap-4 flex-wrap">
          {/* Infos projet */}
          <div className="min-w-0">
            <div className="flex items-center gap-2 mb-1 flex-wrap">
              <h1 className="text-lg font-bold text-slate-900 truncate max-w-lg">{project.title}</h1>
              <StatusBadge status={project.status} />
            </div>

            <div className="flex items-center gap-3 text-xs text-slate-400 flex-wrap">
              {project.buyer && <span className="font-medium text-slate-600">{project.buyer}</span>}
              {deadline && (
                <span className={cn(
                  "flex items-center gap-1",
                  isUrgent ? "text-danger-600 font-semibold" : "text-slate-400"
                )}>
                  <Clock className="w-3 h-3" />
                  {isUrgent ? `⚠ Remise dans ${daysLeft}j` : `Remise : ${formatDate(project.submission_deadline)}`}
                </span>
              )}
              {project.reference && (
                <span className="font-mono bg-slate-100 px-1.5 py-0.5 rounded text-slate-500">
                  {project.reference}
                </span>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2 flex-shrink-0 flex-wrap">
            <ProgressAnalysis status={project.status} />

            {project.status === "analyzing" && (
              <span className="flex items-center gap-1.5 text-xs text-amber-700 bg-amber-50 px-3 py-1.5 rounded-full border border-amber-200">
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                Analyse en cours…
              </span>
            )}

            {canAnalyze && (
              <button
                onClick={handleAnalyze}
                disabled={triggerAnalysis.isPending}
                className="btn-primary-gradient flex items-center gap-2 text-sm"
              >
                {triggerAnalysis.isPending
                  ? <Loader2 className="w-4 h-4 animate-spin" />
                  : project.status === "ready"
                    ? <RefreshCw className="w-4 h-4" />
                    : <Play className="w-4 h-4" />
                }
                {project.status === "ready" ? "Ré-analyser" : "Lancer l'analyse"}
              </button>
            )}

            <Link
              href={`/projects/${projectId}/upload`}
              className="btn-secondary flex items-center gap-2 text-sm"
            >
              <Upload className="w-4 h-4" />
              Ajouter des PDFs
            </Link>
          </div>
        </div>
      </div>

      {/* ── Go/No-Go card (uniquement si ready) ── */}
      {isReady && (
        <div className="px-6 md:px-8 pt-5 pb-0">
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp className="w-4 h-4 text-primary-600" />
            <h2 className="text-sm font-semibold text-slate-700">Score Go/No-Go</h2>
          </div>
          <GoNoGoCard projectId={projectId} />
        </div>
      )}

      {/* ── Win/Loss section (toujours visible) ── */}
      <WinLossSection project={project} />

      {/* ── Tabs (grouped, scroll horizontal sur mobile) ── */}
      <div className="relative border-b border-slate-200 bg-white sticky top-[73px] z-10 mt-5">
        {/* Gradient fade indicators for scroll */}
        <div className="pointer-events-none absolute left-0 top-0 bottom-0 w-6 bg-gradient-to-r from-white to-transparent z-10 md:hidden" />
        <div className="pointer-events-none absolute right-0 top-0 bottom-0 w-6 bg-gradient-to-l from-white to-transparent z-10 md:hidden" />
        <div className="px-4 md:px-8 overflow-x-auto scrollbar-none" role="tablist" aria-label="Onglets d'analyse">
          <div className="flex gap-0 min-w-max">
            {TAB_GROUPS.map((group, gi) => {
              const groupTabs = group.tabs.filter(t => visibleTabs.some(vt => vt.key === t.key));
              if (groupTabs.length === 0) return null;
              return (
                <div key={group.label} className="flex items-center" role="group" aria-label={group.label}>
                  {/* Group separator (not before first group) */}
                  {gi > 0 && (
                    <div className="flex flex-col items-center mx-1.5 self-stretch justify-center" aria-hidden="true">
                      <div className="w-px h-5 bg-slate-200" />
                    </div>
                  )}
                  {/* Group label (hidden on mobile for space) */}
                  <span className="hidden lg:inline text-[9px] font-bold text-slate-300 uppercase tracking-wider px-1.5 self-center select-none" aria-hidden="true">
                    {group.label}
                  </span>
                  {groupTabs.map(({ key, label, icon: Icon }) => (
                    <button
                      key={key}
                      role="tab"
                      aria-selected={activeTab === key}
                      aria-controls={`tabpanel-${key}`}
                      onClick={() => setActiveTab(key)}
                      className={cn(
                        "relative flex items-center gap-1.5 px-3 md:px-4 py-3.5 text-sm font-medium whitespace-nowrap transition-colors duration-150",
                        activeTab === key
                          ? "text-primary-700"
                          : "text-slate-500 hover:text-slate-700"
                      )}
                    >
                      <Icon className="w-4 h-4" aria-hidden="true" />
                      {label}
                      {activeTab === key && (
                        <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-600 rounded-t-full animate-scale-in" aria-hidden="true" />
                      )}
                      {key === "checklist" && isReady && (
                        <span className="ml-0.5 bg-danger-500 text-white text-[9px] font-bold rounded-full w-4 h-4 flex items-center justify-center flex-shrink-0" aria-label="Action requise">
                          !
                        </span>
                      )}
                      {(["chat", "ccap", "rc", "ae", "dc", "conflicts", "questions", "scoring", "pricing", "cctp"].includes(key)) && isReady && (
                        <span className="ml-0.5 bg-primary-600 text-white text-[8px] font-bold rounded-full px-1 flex-shrink-0" aria-label="Analyse IA">
                          IA
                        </span>
                      )}
                    </button>
                  ))}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* ── Tab content ── */}
      <div className="flex-1 p-6 md:p-8" role="tabpanel" id={`tabpanel-${activeTab}`} aria-labelledby={activeTab}>

        {/* Documents tab */}
        {activeTab === "documents" && (
          <div className="max-w-2xl space-y-3 animate-fade-in">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-slate-700">
                {documents?.length || 0} document{(documents?.length || 0) > 1 ? "s" : ""} importé{(documents?.length || 0) > 1 ? "s" : ""}
              </h2>
              <Link
                href={`/projects/${projectId}/upload`}
                className="btn-secondary text-sm flex items-center gap-1.5"
              >
                <Upload className="w-3.5 h-3.5" /> Ajouter
              </Link>
            </div>

            {(!documents || documents.length === 0) ? (
              <div className="empty-state">
                <div className="w-14 h-14 rounded-2xl bg-primary-50 flex items-center justify-center mx-auto mb-4">
                  <FileText className="w-7 h-7 text-primary-300" />
                </div>
                <p className="font-semibold text-slate-700 mb-1">Aucun document importé</p>
                <p className="text-sm text-slate-400 mb-5">
                  Importez vos PDFs (RC, CCTP, CCAP, DPGF…) pour démarrer l&apos;analyse
                </p>
                <Link
                  href={`/projects/${projectId}/upload`}
                  className="btn-primary-gradient inline-flex items-center gap-2"
                >
                  <Upload className="w-4 h-4" /> Importer vos PDFs
                </Link>
              </div>
            ) : (
              documents.map((doc: {
                id: string; original_name: string; doc_type: string | null;
                page_count: number | null; file_size_kb: number | null; status: string;
                ocr_quality_score?: number | null;
              }) => {
                const docStatus = DOC_STATUS[doc.status] ?? DOC_STATUS.pending;
                return (
                  <div key={doc.id} className="space-y-2">
                  <div className={`card p-4 flex items-center justify-between transition-all duration-150 ${docStatus.border}`}>
                    <div className="flex items-center gap-3 min-w-0">
                      <div className="w-8 h-8 bg-slate-50 rounded-lg flex items-center justify-center flex-shrink-0">
                        <FileText className="w-4 h-4 text-slate-400" />
                      </div>
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-slate-800 truncate max-w-xs">{doc.original_name}</p>
                        <p className="text-xs text-slate-400 mt-0.5">
                          {doc.page_count ? `${doc.page_count} pages` : ""}
                          {doc.file_size_kb ? ` · ${(doc.file_size_kb / 1024).toFixed(1)} Mo` : ""}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      {doc.doc_type && (
                        <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${DOC_TYPE_COLORS[doc.doc_type] ?? DOC_TYPE_COLORS.AUTRES}`}>
                          {doc.doc_type}
                        </span>
                      )}
                      <span className={cn(
                        "text-xs px-2 py-0.5 rounded-full font-medium",
                        doc.status === "done"       ? "bg-success-100 text-success-700" :
                        doc.status === "processing" ? "bg-primary-100 text-primary-700" :
                        doc.status === "error"      ? "bg-danger-100 text-danger-700"   :
                                                      "bg-slate-100 text-slate-500"
                      )}>
                        {docStatus.label}
                      </span>
                      {doc.status === "done" && (
                        <button
                          onClick={() => setViewingDoc({ id: doc.id, name: doc.original_name })}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-primary-600 hover:bg-primary-50 transition-colors"
                          title="Visualiser le PDF"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </div>
                  <OcrQualityBanner quality={doc.ocr_quality_score ?? undefined} documentName={doc.original_name} />
                  </div>
                );
              })
            )}
          </div>
        )}

        {/* Summary tab */}
        {activeTab === "summary" && (
          !isReady ? (
            <div className="empty-state animate-fade-in">
              <div className="w-14 h-14 rounded-2xl bg-primary-50 flex items-center justify-center mx-auto mb-4">
                <FileText className="w-7 h-7 text-primary-300" />
              </div>
              <p className="font-semibold text-slate-700 mb-1">Résumé non disponible</p>
              <p className="text-sm text-slate-400">
                {project.status === "analyzing"
                  ? "Analyse IA en cours — résultats disponibles dans 2–5 minutes"
                  : "Importez des documents et lancez l'analyse pour obtenir un résumé"}
              </p>
            </div>
          ) : summary ? (
            <SummaryTab summary={summary} />
          ) : (
            <div className="flex items-center justify-center py-16 gap-2 text-slate-400 text-sm">
              <Loader2 className="w-4 h-4 animate-spin" />
              Chargement du résumé…
            </div>
          )
        )}

        {activeTab === "checklist" && <ChecklistTab projectId={projectId} />}
        {activeTab === "criteria"  && <CriteriaTab  projectId={projectId} />}
        {activeTab === "ccap"      && <CcapRiskTab  projectId={projectId} />}
        {activeTab === "rc"        && <RcAnalysisTab projectId={projectId} />}
        {activeTab === "ae"        && <AeAnalysisTab projectId={projectId} />}
        {activeTab === "cctp"      && <CctpAnalysisTab projectId={projectId} />}
        {activeTab === "dc"        && <DcCheckTab    projectId={projectId} />}
        {activeTab === "conflicts" && <ConflictsTab  projectId={projectId} />}
        {activeTab === "questions" && <QuestionsTab  projectId={projectId} />}
        {activeTab === "scoring"   && <ScoringSimulatorTab projectId={projectId} />}
        {activeTab === "pricing"   && <DpgfPricingTab projectId={projectId} />}
        {activeTab === "cashflow"  && <CashFlowTab  projectId={projectId} />}
        {activeTab === "subcontracting" && <SubcontractingTab projectId={projectId} />}
        {activeTab === "timeline"  && <TimelineTab  projectId={projectId} />}
        {activeTab === "chat"      && <ChatTab      projectId={projectId} />}
        {activeTab === "export"    && <ExportTab    projectId={projectId} projectStatus={project.status} />}
      </div>
    </div>
  );
}
