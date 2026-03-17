"use client";

import { useSubcontracting } from "@/hooks/useAnalysis";
import { AnalysisTabSkeleton } from "@/components/ui/AnalysisSkeleton";
import AIDisclaimer from "@/components/ui/AIDisclaimer";
import ConfidenceWarning from "@/components/ui/ConfidenceWarning";
import { AlertTriangle, CheckCircle2, XCircle, Users, ShieldAlert } from "lucide-react";

const RISK_COLORS: Record<string, string> = {
  faible: "bg-green-100 text-green-800",
  "modéré": "bg-amber-100 text-amber-800",
  "élevé": "bg-red-100 text-red-800",
};

const SEVERITY_COLORS: Record<string, string> = {
  high: "bg-red-100 text-red-800 border-red-200",
  medium: "bg-amber-100 text-amber-800 border-amber-200",
  low: "bg-blue-100 text-blue-800 border-blue-200",
};

interface LotAnalysis {
  lot: string;
  competence_requise: string;
  competence_interne: boolean;
  sous_traitance_recommandee: boolean;
  justification: string;
  risque: string;
}

interface Conflict {
  type: string;
  source_a: string;
  source_b: string;
  description: string;
  severity: string;
}

export function SubcontractingTab({ projectId }: { projectId: string }) {
  const { data, isLoading, error } = useSubcontracting(projectId);

  if (isLoading) return <AnalysisTabSkeleton />;
  if (error) return <p className="text-red-500 text-sm">Erreur de chargement de l&apos;analyse sous-traitance.</p>;
  if (!data) return <p className="text-slate-400 text-sm">Lancez l&apos;analyse pour voir les résultats.</p>;

  const score = data.score_risque ?? 0;
  const scoreColor = score > 60 ? "text-red-600" : score > 30 ? "text-amber-600" : "text-green-600";

  return (
    <div className="space-y-6 animate-fade-in">
      <AIDisclaimer />
      <ConfidenceWarning confidence={data.confidence_overall} />

      {/* Header + Score */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
            <Users className="w-5 h-5 text-primary-600" />
            Analyse Sous-traitance
          </h2>
          <p className="text-sm text-slate-500 mt-1">{data.resume}</p>
        </div>
        <div className="text-center">
          <div className={`text-3xl font-bold ${scoreColor}`} role="meter" aria-valuenow={score} aria-valuemin={0} aria-valuemax={100} aria-label="Score de risque sous-traitance">
            {score}
          </div>
          <p className="text-xs text-slate-400">Risque /100</p>
        </div>
      </div>

      {/* Sous-traitance autorisée */}
      <div className="flex items-center gap-2 p-3 rounded-lg border border-slate-200 bg-slate-50">
        {data.sous_traitance_autorisee ? (
          <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0" />
        ) : (
          <XCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
        )}
        <span className="text-sm font-medium text-slate-700">
          Sous-traitance {data.sous_traitance_autorisee ? "autorisée" : "interdite ou non mentionnée"}
        </span>
        {data.paiement_direct_applicable && (
          <span className="ml-auto text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">
            Paiement direct &ge; {data.seuil_paiement_direct_eur || 600} EUR
          </span>
        )}
      </div>

      {/* Restrictions RC */}
      {data.restrictions_rc && (
        <div className="p-3 rounded-lg border border-amber-200 bg-amber-50">
          <p className="text-sm text-amber-800"><span className="font-medium">Restrictions RC :</span> {data.restrictions_rc}</p>
        </div>
      )}

      {/* Conflits */}
      {data.conflits && data.conflits.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-semibold text-red-800 flex items-center gap-1.5">
            <ShieldAlert className="w-4 h-4" />
            Conflits détectés ({data.conflits.length})
          </h3>
          {data.conflits.map((c: Conflict, i: number) => (
            <div key={i} className={`p-3 rounded-lg border ${SEVERITY_COLORS[c.severity] || SEVERITY_COLORS.medium}`}>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-bold uppercase" aria-label={`Severite du conflit : ${c.severity}`}>{c.severity}</span>
                <span className="text-xs text-slate-500">{c.source_a} vs {c.source_b}</span>
              </div>
              <p className="text-sm">{c.description}</p>
            </div>
          ))}
        </div>
      )}

      {/* Lots analysis */}
      {data.lots_analysis && data.lots_analysis.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-slate-800 mb-3">Analyse par lot</h3>
          <div className="space-y-2">
            {data.lots_analysis.map((lot: LotAnalysis, i: number) => (
              <div key={i} className="p-4 border border-slate-200 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-sm text-slate-900">{lot.lot}</span>
                  <div className="flex items-center gap-2">
                    {lot.sous_traitance_recommandee && (
                      <span className="text-xs bg-primary-100 text-primary-700 px-2 py-0.5 rounded-full">Sous-traiter</span>
                    )}
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full ${RISK_COLORS[lot.risque] || RISK_COLORS.faible}`}
                      aria-label={`Niveau de risque du lot : ${lot.risque}`}
                    >
                      {lot.risque}
                    </span>
                  </div>
                </div>
                <p className="text-xs text-slate-600 mb-1">
                  <span className="font-medium">Compétence requise :</span> {lot.competence_requise}
                </p>
                <p className="text-xs text-slate-500">
                  {lot.competence_interne ? "Compétence interne disponible" : "Compétence interne manquante"} — {lot.justification}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Legal obligations — matching PDF/DOCX report */}
      {data.legal_obligations && data.legal_obligations.length > 0 && (
        <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg">
          <h3 className="text-sm font-semibold text-slate-800 mb-2 flex items-center gap-1.5">
            <ShieldAlert className="w-4 h-4 text-slate-600" />
            Obligations légales
          </h3>
          <ul className="space-y-1">
            {data.legal_obligations.map((o: string, i: number) => (
              <li key={i} className="text-sm text-slate-700 flex items-start gap-2">
                <span className="text-slate-400 mt-1">&#8226;</span>
                {o}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Recommandations */}
      {data.recommandations && data.recommandations.length > 0 && (
        <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <h3 className="text-sm font-semibold text-blue-800 mb-2">Recommandations</h3>
          <ul className="space-y-1">
            {data.recommandations.map((r: string, i: number) => (
              <li key={i} className="text-sm text-blue-700 flex items-start gap-2">
                <span className="text-blue-400 mt-1">&#8226;</span>
                {r}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default SubcontractingTab;
