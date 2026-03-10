"use client";

import {
  AlertTriangle,
  FileX,
  FileCheck2,
  FileText,
  Award,
  ClipboardCheck,
  ListChecks,
  CircleDot,
  CheckCircle2,
  CircleAlert,
} from "lucide-react";
import { useDcCheck } from "@/hooks/useAnalysis";
import { cn } from "@/lib/utils";
import AIDisclaimer from "@/components/ui/AIDisclaimer";

interface Props {
  projectId: string;
}

// ── Types ──────────────────────────────────────────────────────────────────

type DocStatus = "REQUIS" | "FACULTATIF" | "CONDITIONNEL";

interface DocumentRequis {
  document: string;
  obligatoire: boolean;
  format_exige: string | null;
  reference_article: string;
  status: DocStatus;
}

interface CertificationRequise {
  certification: string;
  obligatoire: boolean;
  reference: string;
}

interface Attestation {
  attestation: string;
  validite: string;
  obligatoire: boolean;
}

interface Formulaire {
  formulaire: string;
  version: string;
  reference: string;
}

interface DcCheckData {
  documents_requis: DocumentRequis[];
  certifications_requises: CertificationRequise[];
  attestations: Attestation[];
  formulaires: Formulaire[];
  alertes: string[];
  resume: string;
  model_used?: string;
  no_dc_context?: boolean;
  message?: string;
}

// ── Status config ─────────────────────────────────────────────────────────

const STATUS_CONFIG: Record<DocStatus, {
  label: string;
  badgeCls: string;
  borderCls: string;
  icon: React.ReactNode;
}> = {
  REQUIS: {
    label: "Requis",
    badgeCls: "bg-red-100 text-red-800 border border-red-200",
    borderCls: "border-l-red-500",
    icon: <CircleAlert className="w-3.5 h-3.5 text-red-600" />,
  },
  FACULTATIF: {
    label: "Facultatif",
    badgeCls: "bg-green-100 text-green-800 border border-green-200",
    borderCls: "border-l-green-400",
    icon: <CheckCircle2 className="w-3.5 h-3.5 text-green-600" />,
  },
  CONDITIONNEL: {
    label: "Conditionnel",
    badgeCls: "bg-amber-100 text-amber-800 border border-amber-200",
    borderCls: "border-l-amber-400",
    icon: <CircleDot className="w-3.5 h-3.5 text-amber-600" />,
  },
};

// ── Stat card ─────────────────────────────────────────────────────────────

function StatCard({
  icon,
  label,
  value,
  color,
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
  color: string;
}) {
  return (
    <div className="card p-4 flex items-center gap-3 bg-white">
      <div className={cn("w-10 h-10 rounded-lg flex items-center justify-center shrink-0", color)}>
        {icon}
      </div>
      <div>
        <p className="text-2xl font-bold text-slate-800">{value}</p>
        <p className="text-xs text-slate-500 font-medium">{label}</p>
      </div>
    </div>
  );
}

// ── Document card ─────────────────────────────────────────────────────────

function DocumentCard({ doc, index }: { doc: DocumentRequis; index: number }) {
  const cfg = STATUS_CONFIG[doc.status] ?? STATUS_CONFIG.REQUIS;

  return (
    <div className={cn("card border-l-4 p-4 space-y-1 animate-fade-in bg-white", cfg.borderCls)}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-xs text-slate-400 font-mono w-5 shrink-0">{index + 1}</span>
          <div className="min-w-0">
            <p className="text-sm font-medium text-slate-800 leading-snug">
              {doc.document}
            </p>
            {doc.reference_article && (
              <p className="text-xs text-slate-400 mt-0.5">{doc.reference_article}</p>
            )}
          </div>
        </div>
        <div className="shrink-0">
          <span
            className={cn("inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold", cfg.badgeCls)}
            aria-label={`Statut du document : ${cfg.label}`}
          >
            {cfg.icon}
            {cfg.label}
          </span>
        </div>
      </div>
      {doc.format_exige && (
        <p className="text-xs text-slate-500 ml-7">
          <span className="font-medium text-slate-600">Format exig&eacute; :</span> {doc.format_exige}
        </p>
      )}
    </div>
  );
}

// ── Skeleton loading ──────────────────────────────────────────────────────

function DcSkeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      {/* Header skeleton */}
      <div className="card p-5 space-y-3">
        <div className="h-4 bg-slate-200 rounded w-1/3" />
        <div className="h-3 bg-slate-100 rounded w-full" />
        <div className="h-3 bg-slate-100 rounded w-3/4" />
      </div>
      {/* Stats skeleton */}
      <div className="grid grid-cols-3 gap-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="card p-4 flex items-center gap-3">
            <div className="w-10 h-10 bg-slate-200 rounded-lg" />
            <div className="space-y-1">
              <div className="h-6 w-8 bg-slate-200 rounded" />
              <div className="h-3 w-16 bg-slate-100 rounded" />
            </div>
          </div>
        ))}
      </div>
      {/* Cards skeleton */}
      {[1, 2, 3, 4].map((i) => (
        <div key={i} className="card border-l-4 border-l-slate-200 p-4 space-y-2">
          <div className="h-4 bg-slate-200 rounded w-2/3" />
          <div className="h-3 bg-slate-100 rounded w-full" />
        </div>
      ))}
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────

export function DcCheckTab({ projectId }: Props) {
  const { data, isLoading, isError } = useDcCheck(projectId);

  if (isLoading) return <DcSkeleton />;

  if (isError) {
    return (
      <div className="card p-8 flex flex-col items-center gap-3 text-center animate-fade-in">
        <AlertTriangle className="w-10 h-10 text-amber-400" />
        <p className="text-slate-600 font-medium">Impossible de charger la v&eacute;rification des documents administratifs.</p>
        <p className="text-slate-400 text-sm">V&eacute;rifiez que l&apos;analyse du projet a bien &eacute;t&eacute; lanc&eacute;e.</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="card p-8 flex flex-col items-center gap-3 text-center animate-fade-in">
        <FileX className="w-10 h-10 text-slate-300" />
        <p className="text-slate-500">Aucune donn&eacute;e disponible.</p>
      </div>
    );
  }

  const dcData = data as DcCheckData;

  // Empty state: no DC context
  if (dcData.no_dc_context) {
    return (
      <div className="card p-10 flex flex-col items-center gap-4 text-center animate-fade-in">
        <div className="w-14 h-14 rounded-2xl bg-slate-100 flex items-center justify-center">
          <FileX className="w-7 h-7 text-slate-400" />
        </div>
        <div className="space-y-1">
          <p className="font-semibold text-slate-700">Aucun contexte de documents administratifs</p>
          <p className="text-slate-400 text-sm max-w-sm">
            {dcData.message ?? "Uploadez les pi\u00e8ces du DCE pour activer la v\u00e9rification automatique des documents administratifs requis."}
          </p>
        </div>
      </div>
    );
  }

  const documentsReqius = dcData.documents_requis ?? [];
  const certifications = dcData.certifications_requises ?? [];
  const attestations = dcData.attestations ?? [];
  const formulaires = dcData.formulaires ?? [];
  const alertes = dcData.alertes ?? [];

  // Sort documents: REQUIS first, then CONDITIONNEL, then FACULTATIF
  const STATUS_ORDER: DocStatus[] = ["REQUIS", "CONDITIONNEL", "FACULTATIF"];
  const sortedDocs = [...documentsReqius].sort(
    (a, b) => STATUS_ORDER.indexOf(a.status) - STATUS_ORDER.indexOf(b.status)
  );

  const nbDocsRequis = documentsReqius.filter((d) => d.status === "REQUIS").length;

  return (
    <div className="space-y-4 animate-fade-in">
      {/* ── Header card ── */}
      <div className="card p-5">
        <div className="flex-1 space-y-1">
          <p className="font-semibold text-slate-800 text-base">
            V&eacute;rification des documents administratifs
          </p>
          <p className="text-xs text-slate-400">
            Liste des pi&egrave;ces, certifications et attestations demand&eacute;es par le pouvoir adjudicateur
          </p>
        </div>

        {/* Resume */}
        {dcData.resume && (
          <div className="mt-4 pt-4 border-t border-slate-100">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">
              Synth&egrave;se
            </p>
            <p className="text-sm text-slate-700 leading-relaxed">
              {dcData.resume}
            </p>
          </div>
        )}
      </div>

      {/* ── Summary stats ── */}
      <div className="grid grid-cols-3 gap-3">
        <StatCard
          icon={<FileCheck2 className="w-5 h-5 text-blue-600" />}
          label="Documents requis"
          value={nbDocsRequis}
          color="bg-blue-50"
        />
        <StatCard
          icon={<Award className="w-5 h-5 text-emerald-600" />}
          label="Certifications"
          value={certifications.length}
          color="bg-emerald-50"
        />
        <StatCard
          icon={<AlertTriangle className="w-5 h-5 text-amber-600" />}
          label="Alertes"
          value={alertes.length}
          color="bg-amber-50"
        />
      </div>

      {/* ── Documents requis ── */}
      {sortedDocs.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center gap-2 px-1">
            <ListChecks className="w-4 h-4 text-slate-500" />
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
              Documents requis ({sortedDocs.length})
            </p>
          </div>
          {sortedDocs.map((doc, i) => (
            <DocumentCard key={i} doc={doc} index={i} />
          ))}
        </div>
      )}

      {/* ── Certifications requises ── */}
      {certifications.length > 0 && (
        <div className="card p-4 space-y-3">
          <div className="flex items-center gap-2">
            <Award className="w-4 h-4 text-emerald-600" />
            <p className="text-sm font-semibold text-slate-700">
              Certifications requises ({certifications.length})
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            {certifications.map((cert, i) => (
              <span
                key={i}
                className={cn(
                  "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border",
                  cert.obligatoire
                    ? "bg-red-50 text-red-800 border-red-200"
                    : "bg-slate-50 text-slate-700 border-slate-200"
                )}
              >
                {cert.obligatoire ? (
                  <CircleAlert className="w-3.5 h-3.5 text-red-500" />
                ) : (
                  <CheckCircle2 className="w-3.5 h-3.5 text-slate-400" />
                )}
                <span>{cert.certification}</span>
                {cert.reference && (
                  <span className="text-[10px] text-slate-400 ml-1">({cert.reference})</span>
                )}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* ── Attestations ── */}
      {attestations.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center gap-2 px-1">
            <ClipboardCheck className="w-4 h-4 text-slate-500" />
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
              Attestations ({attestations.length})
            </p>
          </div>
          {attestations.map((att, i) => (
            <div
              key={i}
              className={cn(
                "card border-l-4 p-4 space-y-1 animate-fade-in bg-white",
                att.obligatoire ? "border-l-red-500" : "border-l-slate-300"
              )}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-sm font-medium text-slate-800">{att.attestation}</p>
                  {att.validite && (
                    <p className="text-xs text-slate-500 mt-0.5">
                      <span className="font-medium text-slate-600">Validit&eacute; :</span> {att.validite}
                    </p>
                  )}
                </div>
                <div className="shrink-0">
                  {att.obligatoire ? (
                    <span
                      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-red-100 text-red-800 border border-red-200"
                      aria-label="Attestation : Obligatoire"
                    >
                      <CircleAlert className="w-3.5 h-3.5" />
                      Obligatoire
                    </span>
                  ) : (
                    <span
                      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-600 border border-slate-200"
                      aria-label="Attestation : Recommandee"
                    >
                      Recommand&eacute;e
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ── Formulaires ── */}
      {formulaires.length > 0 && (
        <div className="card p-4 space-y-3">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-blue-600" />
            <p className="text-sm font-semibold text-slate-700">
              Formulaires ({formulaires.length})
            </p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100">
                  <th className="text-left py-2 px-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                    Formulaire
                  </th>
                  <th className="text-left py-2 px-3 text-xs font-semibold text-slate-500 uppercase tracking-wide w-28">
                    Version
                  </th>
                  <th className="text-left py-2 px-3 text-xs font-semibold text-slate-500 uppercase tracking-wide w-32">
                    R&eacute;f&eacute;rence
                  </th>
                </tr>
              </thead>
              <tbody>
                {formulaires.map((form, i) => (
                  <tr key={i} className="border-b border-slate-50 last:border-b-0 hover:bg-slate-50 transition-colors">
                    <td className="py-2 px-3 text-slate-700">{form.formulaire}</td>
                    <td className="py-2 px-3 text-slate-600">{form.version || "\u2014"}</td>
                    <td className="py-2 px-3 text-slate-400 text-xs">{form.reference || "\u2014"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── Alertes ── */}
      {alertes.length > 0 && (
        <div className="card border-l-4 border-l-amber-400 bg-amber-50 p-4 space-y-2">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-600" />
            <p className="text-sm font-semibold text-amber-800">
              {alertes.length === 1 ? "Alerte" : "Alertes"} ({alertes.length})
            </p>
          </div>
          <ul className="space-y-1">
            {alertes.map((alerte, i) => (
              <li key={i} className="text-sm text-amber-700 leading-relaxed flex items-start gap-2">
                <span className="text-amber-400 mt-1 shrink-0">&bull;</span>
                <span>{alerte}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* ── Footer disclaimer ── */}
      <AIDisclaimer />
    </div>
  );
}
