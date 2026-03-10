"use client";

import { useCctpAnalysis } from "@/hooks/useAnalysis";
import { AlertTriangle, CheckCircle2, FileWarning, Info, Loader2, Wrench, Shield, FlaskConical, FileText, Ban } from "lucide-react";
import AIDisclaimer from "@/components/ui/AIDisclaimer";
import ConfidenceWarning from "@/components/ui/ConfidenceWarning";

interface Props {
  projectId: string;
}

const CATEGORY_CONFIG: Record<string, { label: string; icon: typeof Wrench; color: string }> = {
  materiaux: { label: "Matériaux & Fournitures", icon: Wrench, color: "blue" },
  normes: { label: "Normes & DTU", icon: FileText, color: "indigo" },
  execution: { label: "Conditions d'exécution", icon: Wrench, color: "slate" },
  essais: { label: "Essais & Contrôles", icon: FlaskConical, color: "purple" },
  garanties: { label: "Garanties", icon: Shield, color: "green" },
  risques: { label: "Risques techniques", icon: AlertTriangle, color: "red" },
  documents: { label: "Documents d'exécution", icon: FileText, color: "amber" },
  restrictives: { label: "Clauses restrictives", icon: Ban, color: "orange" },
};

const RISK_COLORS: Record<string, string> = {
  CRITIQUE: "bg-red-100 text-red-800 border-red-200",
  HAUT: "bg-orange-100 text-orange-800 border-orange-200",
  MOYEN: "bg-amber-100 text-amber-800 border-amber-200",
  BAS: "bg-green-100 text-green-800 border-green-200",
  INFO: "bg-slate-100 text-slate-700 border-slate-200",
};

const SEVERITY_COLORS: Record<string, string> = {
  CRITIQUE: "border-l-red-500 bg-red-50",
  HAUT: "border-l-orange-500 bg-orange-50",
  MOYEN: "border-l-amber-500 bg-amber-50",
  BAS: "border-l-green-500 bg-green-50",
};

function ComplexityGauge({ score }: { score: number }) {
  const color = score > 80 ? "text-red-600" : score > 60 ? "text-orange-500" : score > 30 ? "text-amber-500" : "text-green-500";
  const label = score > 80 ? "Très complexe" : score > 60 ? "Complexe" : score > 30 ? "Moyen" : "Simple";
  const circumference = 2 * Math.PI * 40;
  const offset = circumference - (score / 100) * circumference;

  return (
    <div className="flex flex-col items-center gap-1">
      <div
        className="relative w-24 h-24"
        role="meter"
        aria-valuenow={score}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`Score de complexite technique : ${score} sur 100 (${label})`}
      >
        <svg className="w-24 h-24 -rotate-90" viewBox="0 0 100 100" aria-hidden="true">
          <circle cx="50" cy="50" r="40" fill="none" stroke="#e5e7eb" strokeWidth="8" />
          <circle cx="50" cy="50" r="40" fill="none" stroke="currentColor"
            className={color} strokeWidth="8" strokeLinecap="round"
            strokeDasharray={circumference} strokeDashoffset={offset} />
        </svg>
        <span className={`absolute inset-0 flex items-center justify-center text-xl font-bold ${color}`}>
          {score}
        </span>
      </div>
      <span className="text-xs text-slate-500 font-medium">{label}</span>
    </div>
  );
}

export default function CctpAnalysisTab({ projectId }: Props) {
  const { data, isLoading, error } = useCctpAnalysis(projectId);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="w-6 h-6 animate-spin text-blue-500 mr-2" />
        <span className="text-sm text-slate-500">Analyse CCTP en cours...</span>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="text-center py-12 text-slate-500">
        <FileWarning className="w-10 h-10 mx-auto mb-2 text-slate-400" />
        <p className="text-sm">
          {data?.no_cctp_document
            ? "Aucun document CCTP trouvé. Uploadez un Cahier des Clauses Techniques."
            : "Erreur lors de l'analyse CCTP."}
        </p>
      </div>
    );
  }

  const exigences = data.exigences_techniques || [];
  const normes = data.normes_dtu_applicables || [];
  const materiaux = data.materiaux_imposes || [];
  const essais = data.essais_controles || [];
  const documents = data.documents_execution || [];
  const risques = data.risques_techniques || [];

  // Group exigences by category
  const grouped = exigences.reduce((acc: Record<string, typeof exigences>, ex: any) => {
    const cat = ex.category || "autre";
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(ex);
    return acc;
  }, {} as Record<string, typeof exigences>);

  return (
    <div className="space-y-6">
      {/* Header avec score complexité */}
      <div className="bg-white rounded-xl border p-6 flex items-start justify-between">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-slate-800 mb-2">Analyse CCTP</h3>
          <p className="text-sm text-slate-600 leading-relaxed">{data.resume || "Aucun résumé disponible."}</p>
          <div className="flex gap-4 mt-4 text-xs text-slate-500">
            <span>{data.nb_exigences || 0} exigences</span>
            <span>{data.nb_normes || 0} normes/DTU</span>
            <span>{data.nb_materiaux_imposes || 0} matériaux imposés</span>
            <span>{data.nb_risques_techniques || 0} risques</span>
            <span>{data.nb_essais || 0} essais requis</span>
          </div>
        </div>
        <ComplexityGauge score={data.score_complexite_technique || 0} />
      </div>

      {/* Alertes anticoncurrentielles */}
      {data.nb_anticoncurrentiel > 0 && (
        <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 flex items-start gap-3">
          <Ban className="w-5 h-5 text-orange-500 shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-orange-800">
              {data.nb_anticoncurrentiel} matériau(x) potentiellement anticoncurrentiel(s)
            </p>
            <p className="text-xs text-orange-600 mt-1">
              Marque imposée sans mention &quot;ou équivalent&quot; — contraire à l&apos;art. R2111-7 du CCP.
            </p>
          </div>
        </div>
      )}

      {/* Risques critiques */}
      {data.nb_risques_critiques > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-red-800">
              {data.nb_risques_critiques} risque(s) technique(s) CRITIQUE(S) détecté(s)
            </p>
            <p className="text-xs text-red-600 mt-1">
              Consultez la section Risques techniques ci-dessous pour les détails.
            </p>
          </div>
        </div>
      )}

      {/* Exigences groupées par catégorie */}
      {Object.entries(grouped).map(([cat, items]) => {
        const config = CATEGORY_CONFIG[cat] || { label: cat, icon: Info, color: "slate" };
        const Icon = config.icon;
        return (
          <div key={cat} className="bg-white rounded-xl border overflow-hidden">
            <div className={`px-4 py-3 border-b bg-${config.color}-50 flex items-center gap-2`}>
              <Icon className={`w-4 h-4 text-${config.color}-600`} />
              <h4 className="text-sm font-semibold text-slate-700">{config.label}</h4>
              <span className="ml-auto text-xs text-slate-400">{(items as any[]).length} exigence(s)</span>
            </div>
            <div className="divide-y">
              {(items as any[]).map((ex: any, i: number) => (
                <div key={i} className="px-4 py-3">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1">
                      <p className="text-sm text-slate-800">{ex.description}</p>
                      {ex.norme_ref && (
                        <span className="inline-block mt-1 text-xs bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded">
                          {ex.norme_ref}
                        </span>
                      )}
                      {ex.conseil && (
                        <p className="text-xs text-slate-500 mt-1 italic">💡 {ex.conseil}</p>
                      )}
                    </div>
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded-full border font-medium shrink-0 ${RISK_COLORS[ex.risk_level] || RISK_COLORS.INFO}`}
                      aria-label={`Niveau de risque : ${ex.risk_level}`}
                    >
                      {ex.risk_level}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      })}

      {/* Normes DTU */}
      {normes.length > 0 && (
        <div className="bg-white rounded-xl border overflow-hidden">
          <div className="px-4 py-3 border-b bg-indigo-50">
            <h4 className="text-sm font-semibold text-slate-700">Normes & DTU applicables</h4>
          </div>
          <div className="p-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {normes.map((n: any, i: number) => (
                <div key={i} className="flex items-start gap-2 p-2 bg-slate-50 rounded-lg">
                  <CheckCircle2 className="w-4 h-4 text-indigo-500 shrink-0 mt-0.5" />
                  <div>
                    <p className="text-xs font-medium text-slate-800">{n.code}</p>
                    <p className="text-[11px] text-slate-500">{n.titre}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Risques techniques */}
      {risques.length > 0 && (
        <div className="bg-white rounded-xl border overflow-hidden">
          <div className="px-4 py-3 border-b bg-red-50">
            <h4 className="text-sm font-semibold text-slate-700">Risques techniques</h4>
          </div>
          <div className="divide-y">
            {risques.map((r: any, i: number) => (
              <div key={i} className={`px-4 py-3 border-l-4 ${SEVERITY_COLORS[r.severity] || ""}`}>
                <div className="flex items-center gap-2 mb-1">
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded-full border font-medium ${RISK_COLORS[r.severity] || RISK_COLORS.MOYEN}`}
                    aria-label={`Severite du risque : ${r.severity}`}
                  >
                    {r.severity}
                  </span>
                  <span className="text-xs text-slate-500 uppercase">{r.type}</span>
                </div>
                <p className="text-sm text-slate-800">{r.description}</p>
                {r.mitigation && (
                  <p className="text-xs text-slate-500 mt-1">🛡️ {r.mitigation}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Matériaux imposés */}
      {materiaux.length > 0 && (
        <div className="bg-white rounded-xl border overflow-hidden">
          <div className="px-4 py-3 border-b bg-blue-50">
            <h4 className="text-sm font-semibold text-slate-700">Matériaux imposés</h4>
          </div>
          <table className="w-full text-xs">
            <thead className="bg-slate-50">
              <tr>
                <th className="text-left px-4 py-2 text-slate-500">Désignation</th>
                <th className="text-center px-2 py-2 text-slate-500">Marque</th>
                <th className="text-center px-2 py-2 text-slate-500">Anticoncurrentiel</th>
                <th className="text-left px-4 py-2 text-slate-500">Alternative</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {materiaux.map((m: any, i: number) => (
                <tr key={i} className={m.anticoncurrentiel ? "bg-orange-50" : ""}>
                  <td className="px-4 py-2 text-slate-800">{m.designation}</td>
                  <td className="px-2 py-2 text-center">{m.marque_imposee ? "⚠️ Oui" : "Non"}</td>
                  <td className="px-2 py-2 text-center">{m.anticoncurrentiel ? "🚫 Oui" : "✅ Non"}</td>
                  <td className="px-4 py-2 text-slate-500">{m.alternative || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Confidence + Footer disclaimer */}
      <ConfidenceWarning confidence={data.confidence_overall} />
      <AIDisclaimer />
    </div>
  );
}
