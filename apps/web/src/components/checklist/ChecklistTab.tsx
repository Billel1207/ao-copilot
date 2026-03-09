"use client";
import { useState } from "react";
import {
  CheckCircle2, XCircle, HelpCircle, AlertOctagon, Info, ChevronDown,
  Sparkles, Copy, Check, X, Loader2,
} from "lucide-react";
import { CitationTooltip } from "@/components/ui/CitationTooltip";
import { ConfidenceBar } from "@/components/ui/ConfidenceBar";
import { useChecklist, useGenerateText, useUpdateChecklistItem } from "@/hooks/useAnalysis";
import { TableSkeleton } from "@/components/common/Skeleton";
import { cn } from "@/lib/utils";

interface Props { projectId: string; }

// ── Badge helpers ───────────────────────────────────────────────────────────
function StatusBadge({ status }: { status: string }) {
  const configs = {
    "OK":          { icon: <CheckCircle2 className="w-3 h-3" />, cls: "badge-ok" },
    "MANQUANT":    { icon: <XCircle className="w-3 h-3" />,      cls: "badge-manquant" },
    "À CLARIFIER": { icon: <HelpCircle className="w-3 h-3" />,   cls: "badge-clarifier" },
  };
  const c = configs[status as keyof typeof configs] ?? { icon: null, cls: "badge-info" };
  return (
    <span className={`badge ${c.cls}`}>
      {c.icon}{status}
    </span>
  );
}

function CriticalityBadge({ criticality }: { criticality: string | null }) {
  if (!criticality) return <span className="badge-info">—</span>;
  const configs: Record<string, { cls: string; icon: React.ReactNode }> = {
    "Éliminatoire": { cls: "badge-critique",  icon: <AlertOctagon className="w-3 h-3" /> },
    "Important":    { cls: "badge-important", icon: <AlertOctagon className="w-3 h-3" /> },
    "Info":         { cls: "badge-info",      icon: <Info className="w-3 h-3" /> },
  };
  const c = configs[criticality] ?? { cls: "badge-info", icon: null };
  return <span className={`badge ${c.cls}`}>{c.icon}{criticality}</span>;
}

// ── Pill filter button ─────────────────────────────────────────────────────
function FilterPill({
  label, count, active, colorClass, onClick,
}: {
  label: string; count: number; active: boolean; colorClass: string; onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold
        border transition-all duration-150
        ${active
          ? `${colorClass} shadow-sm border-current/30`
          : "bg-white border-slate-200 text-slate-500 hover:border-slate-300 hover:bg-slate-50"
        }`}
    >
      {label}
      <span className={`px-1.5 py-0.5 rounded-full text-[10px] font-bold
        ${active ? "bg-white/30" : "bg-slate-100 text-slate-600"}`}>
        {count}
      </span>
    </button>
  );
}

// ── Writing Assistant Modal ──────────────────────────────────────────────────
function WritingModal({
  text,
  onClose,
}: {
  text: string;
  onClose: () => void;
}) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-fade-in">
      <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full animate-slide-up">

        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-primary-100 flex items-center justify-center">
              <Sparkles className="w-3.5 h-3.5 text-primary-700" />
            </div>
            <p className="font-semibold text-slate-800 text-sm">Texte généré par l&apos;IA</p>
          </div>
          <button
            onClick={onClose}
            className="w-7 h-7 rounded-lg hover:bg-slate-100 flex items-center justify-center text-slate-400 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-5">
          <div className="bg-slate-50 rounded-xl p-4 text-sm text-slate-700 leading-relaxed whitespace-pre-wrap border border-slate-200">
            {text}
          </div>
          <p className="text-[10px] text-slate-400 mt-2">
            ✦ Révisez et adaptez ce texte avant de l&apos;utiliser dans votre offre.
          </p>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-end gap-2 px-5 pb-4">
          <button
            onClick={onClose}
            className="btn-secondary text-sm"
          >
            Fermer
          </button>
          <button
            onClick={handleCopy}
            className={cn(
              "flex items-center gap-1.5 text-sm px-4 py-2 rounded-xl font-semibold transition-all",
              copied
                ? "bg-success-100 text-success-700 border border-success-200"
                : "btn-primary-gradient"
            )}
          >
            {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
            {copied ? "Copié !" : "Copier"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Main Component ─────────────────────────────────────────────────────────
export function ChecklistTab({ projectId }: Props) {
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [critFilter, setCritFilter]     = useState<string>("");
  const [expanded, setExpanded]         = useState<Set<string>>(new Set());
  const [generatedText, setGeneratedText] = useState<string | null>(null);
  const [generatingId, setGeneratingId]   = useState<string | null>(null);

  const filters = { status: statusFilter, criticality: critFilter, category: "" };
  const { data, isLoading } = useChecklist(projectId, filters);
  const generateText = useGenerateText(projectId);
  const updateItem = useUpdateChecklistItem(projectId);

  const toggleExpand = (id: string) => {
    setExpanded(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const handleGenerate = async (itemId: string) => {
    setGeneratingId(itemId);
    try {
      const result = await generateText.mutateAsync(itemId);
      setGeneratedText(result.generated_text);
    } catch (e: unknown) {
      const err = e as { response?: { status?: number } };
      if (err?.response?.status === 403) {
        setGeneratedText("⚠️ L'assistant rédaction est disponible à partir du plan Pro. Upgradez votre plan pour accéder à cette fonctionnalité.");
      } else {
        setGeneratedText("Une erreur est survenue lors de la génération. Veuillez réessayer.");
      }
    } finally {
      setGeneratingId(null);
    }
  };

  if (isLoading) return <TableSkeleton rows={6} />;
  if (!data) return (
    <div className="empty-state">
      <p>Aucune donnée disponible — lancez l&apos;analyse d&apos;abord.</p>
    </div>
  );

  const { by_status, by_criticality, total, checklist } = data;

  return (
    <>
      {generatedText && (
        <WritingModal text={generatedText} onClose={() => setGeneratedText(null)} />
      )}

      <div className="space-y-4 animate-fade-in">
        {/* ── Stats pills ── */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2 flex-wrap">
            <FilterPill label="Tous"       count={total}                      active={statusFilter === ""}           colorClass="bg-primary-100 text-primary-800" onClick={() => setStatusFilter("")} />
            <FilterPill label="Manquants"  count={by_status?.["MANQUANT"] ?? 0}    active={statusFilter === "MANQUANT"}   colorClass="bg-danger-100 text-danger-700"   onClick={() => setStatusFilter(statusFilter === "MANQUANT" ? "" : "MANQUANT")} />
            <FilterPill label="À clarifier" count={by_status?.["À CLARIFIER"] ?? 0} active={statusFilter === "À CLARIFIER"} colorClass="bg-warning-100 text-warning-700" onClick={() => setStatusFilter(statusFilter === "À CLARIFIER" ? "" : "À CLARIFIER")} />
            <FilterPill label="OK"          count={by_status?.["OK"] ?? 0}          active={statusFilter === "OK"}          colorClass="bg-success-100 text-success-700" onClick={() => setStatusFilter(statusFilter === "OK" ? "" : "OK")} />
          </div>

          <div className="h-4 w-px bg-slate-200 hidden md:block" />

          <div className="flex items-center gap-2 flex-wrap">
            <FilterPill label="Éliminatoires" count={by_criticality?.["Éliminatoire"] ?? 0} active={critFilter === "Éliminatoire"} colorClass="bg-danger-600 text-white"   onClick={() => setCritFilter(critFilter === "Éliminatoire" ? "" : "Éliminatoire")} />
            <FilterPill label="Importants"    count={by_criticality?.["Important"] ?? 0}    active={critFilter === "Important"}    colorClass="bg-warning-600 text-white" onClick={() => setCritFilter(critFilter === "Important" ? "" : "Important")} />
          </div>
        </div>

        {/* ── Table ── */}
        <div className="card overflow-hidden">
          {checklist.length === 0 ? (
            <div className="empty-state py-12">
              <CheckCircle2 className="w-10 h-10 text-slate-200 mb-3" />
              <p className="text-slate-400 text-sm">Aucune exigence correspondant aux filtres</p>
            </div>
          ) : (
            <>
              {/* Header */}
              <div className="grid grid-cols-[auto,1fr,auto,auto,auto] gap-x-4 px-4 py-3
                              bg-slate-50 border-b border-slate-100 text-xs font-semibold text-slate-500
                              uppercase tracking-wide">
                <span className="w-6">#</span>
                <span>Exigence</span>
                <span className="hidden md:block w-28">Criticité</span>
                <span className="w-28">Statut</span>
                <span className="hidden lg:block w-20">Confiance</span>
              </div>

              {/* Rows */}
              <div className="divide-y divide-slate-50">
                {checklist.map((item: {
                  id: string;
                  requirement: string;
                  what_to_provide: string | null;
                  citations: Array<{ doc: string; page: number; quote: string }>;
                  category: string | null;
                  criticality: string | null;
                  status: string;
                  confidence: number | null;
                }, i: number) => {
                  const isOpen = expanded.has(item.id);
                  const isGenerating = generatingId === item.id;
                  const showGenerateBtn = item.status === "MANQUANT";

                  return (
                    <div
                      key={item.id}
                      className={cn(
                        "checklist-row transition-all",
                        item.criticality === "Éliminatoire" ? "border-l-2 border-l-danger-500" :
                        item.criticality === "Important"    ? "border-l-2 border-l-warning-500" :
                        "border-l-2 border-l-transparent"
                      )}
                    >
                      <button
                        className="w-full grid grid-cols-[auto,1fr,auto,auto,auto] gap-x-4
                                   px-4 py-3.5 text-left items-center"
                        onClick={() => toggleExpand(item.id)}
                      >
                        <span className="w-6 text-xs text-slate-400 font-mono">{i + 1}</span>

                        <div className="min-w-0">
                          <p className="text-sm font-medium text-slate-800 leading-snug line-clamp-2">
                            {item.requirement}
                          </p>
                          {item.category && (
                            <p className="text-xs text-slate-400 mt-0.5">{item.category}</p>
                          )}
                        </div>

                        <div className="hidden md:block w-28">
                          <CriticalityBadge criticality={item.criticality} />
                        </div>

                        <div className="w-28">
                          <StatusBadge status={item.status} />
                        </div>

                        <div className="hidden lg:flex items-center gap-2 w-20">
                          <ConfidenceBar confidence={item.confidence} />
                          <ChevronDown className={cn(
                            "w-3.5 h-3.5 text-slate-300 transition-transform duration-200",
                            isOpen && "rotate-180"
                          )} />
                        </div>
                      </button>

                      {/* Expanded detail */}
                      {isOpen && (
                        <div className="px-4 pb-4 pt-0 ml-10 animate-fade-in space-y-3">
                          {item.what_to_provide && (
                            <div className="bg-primary-50 rounded-lg p-3">
                              <p className="text-xs font-semibold text-primary-700 mb-1">À fournir :</p>
                              <p className="text-xs text-slate-700">{item.what_to_provide}</p>
                            </div>
                          )}

                          {item.citations?.length > 0 && (
                            <div className="flex items-center gap-2">
                              <span className="text-xs text-slate-400">Source :</span>
                              <CitationTooltip citations={item.citations} />
                            </div>
                          )}

                          {/* ── Status change buttons ── */}
                          <div className="flex items-center gap-2 pt-1">
                            <span className="text-xs text-slate-400 font-medium">Statut :</span>
                            {(["OK", "À CLARIFIER", "MANQUANT"] as const).map(s => (
                              <button
                                key={s}
                                disabled={updateItem.isPending}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  updateItem.mutate({ itemId: item.id, data: { status: s } });
                                }}
                                className={cn(
                                  "inline-flex items-center gap-1 text-[11px] font-semibold px-2.5 py-1 rounded-full border transition-all",
                                  item.status === s
                                    ? s === "OK"          ? "bg-success-600 text-white border-success-600"
                                    : s === "MANQUANT"    ? "bg-danger-600 text-white border-danger-600"
                                    :                       "bg-warning-500 text-white border-warning-500"
                                    : "bg-white text-slate-500 border-slate-200 hover:bg-slate-50"
                                )}
                              >
                                {s === "OK" && <CheckCircle2 className="w-3 h-3" />}
                                {s === "MANQUANT" && <XCircle className="w-3 h-3" />}
                                {s === "À CLARIFIER" && <HelpCircle className="w-3 h-3" />}
                                {s}
                              </button>
                            ))}
                            {updateItem.isPending && <Loader2 className="w-3 h-3 animate-spin text-primary-400" />}
                          </div>

                          {/* Writing assistant button */}
                          {showGenerateBtn && (
                            <button
                              onClick={() => handleGenerate(item.id)}
                              disabled={isGenerating}
                              className={cn(
                                "inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg border transition-all",
                                isGenerating
                                  ? "bg-primary-50 text-primary-400 border-primary-100 cursor-not-allowed"
                                  : "bg-primary-700 text-white border-primary-700 hover:bg-primary-800 shadow-sm"
                              )}
                            >
                              {isGenerating
                                ? <><Loader2 className="w-3 h-3 animate-spin" />Génération…</>
                                : <><Sparkles className="w-3 h-3" />✨ Générer une réponse</>
                              }
                            </button>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </>
          )}
        </div>
      </div>
    </>
  );
}
