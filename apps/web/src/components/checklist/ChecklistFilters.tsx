"use client";
import { cn } from "@/lib/utils";

interface Filters {
  criticality: string;
  status: string;
  category: string;
}

interface Props {
  filters: Filters;
  onChange: (filters: Filters) => void;
  stats: { by_status: Record<string, number>; by_criticality: Record<string, number> };
}

const CHIPS = [
  { group: "criticality", value: "", label: "Toutes criticités" },
  { group: "criticality", value: "Éliminatoire", label: "🔴 Éliminatoires" },
  { group: "criticality", value: "Important", label: "🟡 Importants" },
  { group: "criticality", value: "Info", label: "ℹ️ Info" },
];

const STATUS_CHIPS = [
  { value: "", label: "Tous statuts" },
  { value: "MANQUANT", label: "Manquants" },
  { value: "À CLARIFIER", label: "À clarifier" },
  { value: "OK", label: "OK" },
];

const CATEGORIES = [
  { value: "", label: "Toutes catégories" },
  { value: "Administratif", label: "Administratif" },
  { value: "Technique", label: "Technique" },
  { value: "Financier", label: "Financier" },
  { value: "Planning", label: "Planning" },
];

export function ChecklistFilters({ filters, onChange, stats }: Props) {
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        {CHIPS.map((chip) => (
          <button
            key={chip.value}
            onClick={() => onChange({ ...filters, criticality: chip.value })}
            className={cn(
              "text-xs px-3 py-1.5 rounded-full border font-medium transition-colors",
              filters.criticality === chip.value
                ? "bg-primary-800 text-white border-primary-800"
                : "bg-white text-slate-600 border-slate-200 hover:bg-slate-50"
            )}
          >
            {chip.label}
            {chip.value && stats.by_criticality[chip.value] !== undefined && (
              <span className="ml-1 opacity-60">({stats.by_criticality[chip.value]})</span>
            )}
          </button>
        ))}
      </div>
      <div className="flex flex-wrap gap-2">
        {STATUS_CHIPS.map((chip) => (
          <button
            key={chip.value}
            onClick={() => onChange({ ...filters, status: chip.value })}
            className={cn(
              "text-xs px-3 py-1.5 rounded-full border font-medium transition-colors",
              filters.status === chip.value
                ? "bg-slate-800 text-white border-slate-800"
                : "bg-white text-slate-600 border-slate-200 hover:bg-slate-50"
            )}
          >
            {chip.label}
            {chip.value && stats.by_status[chip.value] !== undefined && (
              <span className="ml-1 opacity-60">({stats.by_status[chip.value]})</span>
            )}
          </button>
        ))}
        {CATEGORIES.slice(1).map((cat) => (
          <button
            key={cat.value}
            onClick={() => onChange({ ...filters, category: filters.category === cat.value ? "" : cat.value })}
            className={cn(
              "text-xs px-3 py-1.5 rounded-full border font-medium transition-colors",
              filters.category === cat.value
                ? "bg-slate-800 text-white border-slate-800"
                : "bg-white text-slate-600 border-slate-200 hover:bg-slate-50"
            )}
          >
            {cat.label}
          </button>
        ))}
      </div>
    </div>
  );
}
