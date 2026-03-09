"use client";
import { CitationTooltip } from "@/components/ui/CitationTooltip";
import { useCriteria } from "@/hooks/useAnalysis";

interface Props {
  projectId: string;
}

export function CriteriaTab({ projectId }: Props) {
  const { data, isLoading } = useCriteria(projectId);

  if (isLoading) return <div className="text-center py-12 text-slate-400">Chargement des critères...</div>;
  if (!data?.evaluation) return <div className="text-center py-12 text-slate-400">Aucune donnée disponible</div>;

  const { eligibility_conditions, scoring_criteria, total_weight_check } = data.evaluation;
  const totalWeight = total_weight_check || scoring_criteria?.reduce((s: number, c: { weight_percent: number | null }) => s + (c.weight_percent || 0), 0);

  return (
    <div className="space-y-6">
      {/* Conditions éligibilité */}
      {eligibility_conditions?.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-slate-700 mb-3">Conditions d&apos;éligibilité</h3>
          <div className="card overflow-hidden">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-slate-100 bg-slate-50">
                  <th className="text-left px-4 py-3 font-semibold text-slate-500">Condition</th>
                  <th className="text-left px-4 py-3 font-semibold text-slate-500 w-24">Type</th>
                  <th className="text-left px-4 py-3 font-semibold text-slate-500 w-24">Source</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {eligibility_conditions.map((c: { condition: string; type: string; citations: Array<{ doc: string; page: number; quote: string }> }, i: number) => (
                  <tr key={i} className="hover:bg-slate-50">
                    <td className="px-4 py-3 text-slate-700">{c.condition}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${
                        c.type === "hard" ? "bg-red-100 text-red-700" : "bg-amber-100 text-amber-700"
                      }`}>
                        {c.type === "hard" ? "Éliminatoire" : "Préférentiel"}
                      </span>
                    </td>
                    <td className="px-4 py-3"><CitationTooltip citations={c.citations || []} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Critères de notation */}
      {scoring_criteria?.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-slate-700">Critères de notation</h3>
            {totalWeight !== null && (
              <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                Math.abs(totalWeight - 100) < 1 ? "bg-green-100 text-green-700" : "bg-amber-100 text-amber-700"
              }`}>
                Total : {totalWeight.toFixed(0)}%
              </span>
            )}
          </div>
          <div className="card overflow-hidden">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-slate-100 bg-slate-50">
                  <th className="text-left px-4 py-3 font-semibold text-slate-500">Critère</th>
                  <th className="text-left px-4 py-3 font-semibold text-slate-500 w-24">Pondération</th>
                  <th className="text-left px-4 py-3 font-semibold text-slate-500">Notes</th>
                  <th className="text-left px-4 py-3 font-semibold text-slate-500 w-24">Source</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {scoring_criteria.map((c: { criterion: string; weight_percent: number | null; notes: string | null; citations: Array<{ doc: string; page: number; quote: string }> }, i: number) => (
                  <tr key={i} className="hover:bg-slate-50">
                    <td className="px-4 py-3 font-medium text-slate-700">{c.criterion}</td>
                    <td className="px-4 py-3">
                      {c.weight_percent !== null ? (
                        <div className="flex items-center gap-2">
                          <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden max-w-16">
                            <div className="h-full bg-primary-500 rounded-full" style={{ width: `${c.weight_percent}%` }} />
                          </div>
                          <span className="font-semibold text-primary-800">{c.weight_percent}%</span>
                        </div>
                      ) : (
                        <span className="text-slate-400">Non spécifiée</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-slate-500">{c.notes || "—"}</td>
                    <td className="px-4 py-3"><CitationTooltip citations={c.citations || []} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
