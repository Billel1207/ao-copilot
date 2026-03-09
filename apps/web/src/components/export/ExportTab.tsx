"use client";
import { useState, useRef, useEffect } from "react";
import { Download, Loader2, FileText, Lock, FileOutput, CheckCircle2, Zap, TableProperties, FileEdit } from "lucide-react";
import { toast } from "sonner";
import { exportApi } from "@/lib/api";
import Link from "next/link";

const MAX_POLL_ATTEMPTS = 30;

interface Props {
  projectId: string;
  projectStatus: string;
  userPlan?: string;
  /** Vrai si le projet contient au moins un document classifié DPGF ou BPU */
  hasDpgfDocs?: boolean;
}

// ── Export Card ────────────────────────────────────────────────────────
function ExportCard({
  icon,
  title,
  subtitle,
  features,
  action,
  locked,
  lockedMsg,
}: {
  icon: React.ReactNode;
  title: string;
  subtitle: string;
  features: string[];
  action: React.ReactNode;
  locked?: boolean;
  lockedMsg?: string;
}) {
  return (
    <div className={`card p-6 flex flex-col gap-5 relative overflow-hidden
      ${locked ? "opacity-80" : "hover:shadow-card-hover transition-shadow duration-150"}`}>
      {locked && (
        <div className="absolute inset-0 bg-white/40 backdrop-blur-[1px] rounded-2xl flex items-center justify-center z-10">
          <div className="bg-white border border-slate-200 rounded-xl px-4 py-3 shadow-elevation text-center max-w-xs">
            <Lock className="w-5 h-5 text-warning-600 mx-auto mb-1.5" />
            <p className="text-sm font-semibold text-slate-800">Plan Pro requis</p>
            <p className="text-xs text-slate-500 mt-0.5 mb-3">{lockedMsg}</p>
            <Link href="/billing" className="btn-primary-gradient text-xs py-1.5 px-3 inline-flex items-center gap-1.5">
              <Zap className="w-3 h-3" /> Passer au Pro
            </Link>
          </div>
        </div>
      )}

      <div className="flex items-start gap-4">
        <div className="p-3 bg-primary-50 rounded-xl text-primary-700 flex-shrink-0">
          {icon}
        </div>
        <div>
          <h4 className="font-bold text-slate-900">{title}</h4>
          <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>
        </div>
      </div>

      <ul className="space-y-1.5">
        {features.map((f, i) => (
          <li key={i} className="flex items-center gap-2 text-xs text-slate-600">
            <CheckCircle2 className="w-3.5 h-3.5 text-success-500 flex-shrink-0" />
            {f}
          </li>
        ))}
      </ul>

      <div className="mt-auto">{action}</div>
    </div>
  );
}

// ── Progress indicator ─────────────────────────────────────────────────
function GeneratingProgress({ label }: { label: string }) {
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 text-sm text-slate-600">
        <Loader2 className="w-4 h-4 animate-spin text-primary-600" />
        <span>{label}</span>
      </div>
      <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
        <div className="h-full bg-primary-600 rounded-full animate-pulse-soft w-2/3" />
      </div>
    </div>
  );
}

// ── Main Component ─────────────────────────────────────────────────────
export function ExportTab({
  projectId,
  projectStatus,
  userPlan = "starter",
  hasDpgfDocs = false,
}: Props) {
  const [loadingPdf, setLoadingPdf] = useState(false);
  const [loadingWord, setLoadingWord] = useState(false);
  const [loadingDpgf, setLoadingDpgf] = useState(false);
  const [loadingMemo, setLoadingMemo] = useState(false);
  const [downloadUrlPdf, setDownloadUrlPdf] = useState<string | null>(null);
  const [downloadUrlWord, setDownloadUrlWord] = useState<string | null>(null);
  const abortedRef = useRef(false);
  const isReady = projectStatus === "ready";
  const hasProAccess = userPlan === "pro" || userPlan === "business";

  useEffect(() => {
    abortedRef.current = false;
    return () => { abortedRef.current = true; };
  }, []);

  const pollExport = async (
    startFn: () => Promise<{ data: { job_id: string } }>,
    setLoading: (v: boolean) => void,
    setUrl: (url: string) => void,
    label: string
  ) => {
    if (!isReady) {
      toast.error("L'analyse doit être terminée avant d'exporter");
      return;
    }
    setLoading(true);
    abortedRef.current = false;
    try {
      const { data } = await startFn();
      const jobId = data.job_id;
      let attempts = 0;

      const poll = async (): Promise<void> => {
        if (abortedRef.current) return;
        if (attempts >= MAX_POLL_ATTEMPTS) {
          toast.error(`Génération ${label} trop longue. Réessayez.`);
          setLoading(false);
          return;
        }
        attempts++;
        const { data: status } = await exportApi.getStatus(projectId, jobId);
        if (status.status === "done") {
          setUrl(status.url);
          toast.success(`${label} prêt !`);
          setLoading(false);
        } else if (status.status === "error") {
          toast.error(`Erreur lors de la génération ${label}`);
          setLoading(false);
        } else {
          await new Promise(r => setTimeout(r, 2000));
          return poll();
        }
      };
      await poll();
    } catch {
      toast.error(`Erreur lors de l'export ${label}`);
      setLoading(false);
    }
  };

  /**
   * Téléchargement direct DPGF Excel : la route retourne un StreamingResponse
   * (blob), on crée un object URL temporaire pour déclencher le téléchargement.
   */
  const downloadDpgfExcel = async () => {
    if (!isReady) {
      toast.error("L'analyse doit être terminée avant d'exporter");
      return;
    }
    setLoadingDpgf(true);
    try {
      const response = await exportApi.startDpgfExcel(projectId);
      const blob = new Blob([response.data as BlobPart], {
        type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      });
      const objectUrl = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = objectUrl;
      anchor.download = `DPGF_export.xlsx`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(objectUrl);
      toast.success("Fichier Excel DPGF téléchargé !");
    } catch (err: unknown) {
      // Tenter de lire le message d'erreur JSON depuis la réponse blob
      const axiosError = err as { response?: { data?: Blob; status?: number } };
      if (axiosError?.response?.status === 403) {
        toast.error("Plan Pro requis pour l'export DPGF Excel.");
      } else if (axiosError?.response?.status === 404) {
        toast.error("Aucun document DPGF ou BPU trouvé dans ce projet.");
      } else {
        toast.error("Erreur lors de la génération du fichier Excel DPGF.");
      }
    } finally {
      setLoadingDpgf(false);
    }
  };

  /**
   * Téléchargement direct Mémoire Technique : la route retourne un StreamingResponse
   * (blob .docx), on crée un object URL temporaire pour déclencher le téléchargement.
   */
  const downloadMemoTechnique = async () => {
    if (!isReady) {
      toast.error("L'analyse doit être terminée avant d'exporter");
      return;
    }
    setLoadingMemo(true);
    try {
      const response = await exportApi.startMemo(projectId);
      const blob = new Blob([response.data as BlobPart], {
        type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      });
      const objectUrl = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = objectUrl;
      anchor.download = `memo_technique.docx`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(objectUrl);
      toast.success("Mémoire technique téléchargée !");
    } catch (err: unknown) {
      const axiosError = err as { response?: { status?: number } };
      if (axiosError?.response?.status === 403) {
        toast.error("Plan Pro requis pour la mémoire technique.");
      } else {
        toast.error("Erreur lors de la génération de la mémoire technique.");
      }
    } finally {
      setLoadingMemo(false);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h3 className="text-base font-semibold text-slate-800 mb-1">Exporter le rapport</h3>
        <p className="text-sm text-slate-500">
          Générez votre rapport complet (résumé, checklist, critères) dans le format de votre choix.
        </p>
      </div>

      {!isReady && (
        <div className="flex items-center gap-2 text-sm text-warning-700 bg-warning-50 border border-warning-200
                        rounded-xl px-4 py-3">
          <Loader2 className="w-4 h-4 flex-shrink-0" />
          L&apos;analyse doit être terminée pour pouvoir exporter.
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-3xl">
        {/* ── Export PDF ── */}
        <ExportCard
          icon={<FileText className="w-6 h-6" />}
          title="Rapport PDF"
          subtitle="Idéal pour partager et imprimer"
          features={[
            "Résumé exécutif mis en page",
            "Checklist de conformité complète",
            "Critères de notation",
            "Disponible sur tous les plans",
          ]}
          action={
            downloadUrlPdf ? (
              <a href={downloadUrlPdf} download
                className="btn-primary inline-flex items-center gap-2">
                <Download className="w-4 h-4" /> Télécharger PDF
              </a>
            ) : loadingPdf ? (
              <GeneratingProgress label="Génération PDF en cours..." />
            ) : (
              <button
                onClick={() => pollExport(
                  () => exportApi.startPdf(projectId),
                  setLoadingPdf, setDownloadUrlPdf, "PDF"
                )}
                disabled={!isReady}
                className="btn-primary inline-flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <FileOutput className="w-4 h-4" /> Générer le PDF
              </button>
            )
          }
        />

        {/* ── Export Word ── */}
        <ExportCard
          icon={<FileText className="w-6 h-6" />}
          title="Rapport Word"
          subtitle="Modifiable dans Word ou LibreOffice"
          features={[
            "Même contenu que le PDF",
            "Entièrement éditable (.docx)",
            "Tableaux copiables",
            "Plan Pro ou supérieur",
          ]}
          locked={!hasProAccess}
          lockedMsg="L'export Word est disponible à partir du plan Pro (199€/mois)."
          action={
            downloadUrlWord ? (
              <a href={downloadUrlWord} download
                className="btn-primary inline-flex items-center gap-2">
                <Download className="w-4 h-4" /> Télécharger Word
              </a>
            ) : loadingWord ? (
              <GeneratingProgress label="Génération Word en cours..." />
            ) : (
              <button
                onClick={() => pollExport(
                  () => exportApi.startWord(projectId),
                  setLoadingWord, setDownloadUrlWord, "Word"
                )}
                disabled={!isReady || !hasProAccess}
                className="btn-primary inline-flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <FileOutput className="w-4 h-4" /> Générer le Word
              </button>
            )
          }
        />

        {/* ── Mémoire Technique ── */}
        <div className="relative">
          {/* Badge IA */}
          <span className="absolute top-3 right-3 z-20 inline-flex items-center
            bg-success-500 text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full
            leading-none shadow-sm">
            IA
          </span>
          <ExportCard
            icon={<FileEdit className="w-6 h-6" />}
            title="Mémoire Technique"
            subtitle="Template Word pré-rempli par l'analyse IA — personnalisez ensuite"
            features={[
              "Page de garde + 6 sections structurées",
              "Compréhension du besoin issue du CCTP",
              "Critères d'éligibilité extraits automatiquement",
              "Planning prévisionnel basé sur les dates clés",
              "Plan Pro ou supérieur",
            ]}
            locked={!hasProAccess}
            lockedMsg="La mémoire technique IA est disponible à partir du plan Pro (199€/mois)."
            action={
              loadingMemo ? (
                <GeneratingProgress label="Génération de la mémoire..." />
              ) : (
                <button
                  onClick={downloadMemoTechnique}
                  disabled={!isReady || !hasProAccess}
                  className="btn-primary inline-flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <FileEdit className="w-4 h-4" /> Générer la mémoire
                </button>
              )
            }
          />
        </div>

        {/* ── Export DPGF Excel ── (visible seulement si le projet a des docs DPGF/BPU) */}
        {hasDpgfDocs && (
          <ExportCard
            icon={<TableProperties className="w-6 h-6" />}
            title="DPGF / BPU en Excel"
            subtitle="Tableaux chiffrés prêts à remplir"
            features={[
              "Extraction automatique des tableaux PDF",
              "Colonnes normalisées (N°, Désignation, Qté, PU, Montant HT)",
              "Formatage numérique et total HT calculé",
              "Plan Pro ou supérieur",
            ]}
            locked={!hasProAccess}
            lockedMsg="L'export DPGF Excel est disponible à partir du plan Pro (199€/mois)."
            action={
              loadingDpgf ? (
                <GeneratingProgress label="Extraction DPGF en cours..." />
              ) : (
                <button
                  onClick={downloadDpgfExcel}
                  disabled={!isReady || !hasProAccess}
                  className="btn-primary inline-flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Download className="w-4 h-4" /> Exporter DPGF en Excel
                </button>
              )
            }
          />
        )}
      </div>
    </div>
  );
}
