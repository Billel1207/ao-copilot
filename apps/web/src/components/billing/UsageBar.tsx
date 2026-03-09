"use client";

import { BillingUsage } from "@/stores/billing";

interface UsageBarProps {
  usage: BillingUsage;
  compact?: boolean;
}

const MONTH_NAMES = [
  "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
  "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
];

function getBarColor(pct: number): string {
  if (pct >= 90) return "bg-red-500";
  if (pct >= 75) return "bg-amber-500";
  return "bg-blue-600";
}

function getTextColor(pct: number): string {
  if (pct >= 90) return "text-red-600";
  if (pct >= 75) return "text-amber-600";
  return "text-blue-600";
}

export default function UsageBar({ usage, compact = false }: UsageBarProps) {
  const {
    docs_used_this_month,
    docs_quota,
    quota_pct,
    period_year,
    period_month,
  } = usage;

  const monthName = MONTH_NAMES[period_month - 1] ?? "";
  const barColor = getBarColor(quota_pct);
  const textColor = getTextColor(quota_pct);
  const pctClamped = Math.min(100, quota_pct);

  if (compact) {
    return (
      <div className="w-full">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs text-gray-500">Documents ce mois</span>
          <span className={`text-xs font-semibold ${textColor}`}>
            {docs_used_this_month}/{docs_quota}
          </span>
        </div>
        <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${barColor}`}
            style={{ width: `${pctClamped}%` }}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-gray-100 p-5 shadow-sm">
      <div className="flex items-start justify-between mb-4">
        <div>
          <p className="text-sm font-medium text-gray-500">Utilisation mensuelle</p>
          <p className="text-xs text-gray-400 mt-0.5">
            {monthName} {period_year}
          </p>
        </div>
        <div className="text-right">
          <span className={`text-2xl font-bold ${textColor}`}>{docs_used_this_month}</span>
          <span className="text-gray-400 text-sm font-normal">/{docs_quota} docs</span>
        </div>
      </div>

      {/* Barre de progression */}
      <div className="relative h-3 bg-gray-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ease-out ${barColor}`}
          style={{ width: `${pctClamped}%` }}
        />
      </div>

      <div className="flex items-center justify-between mt-2">
        <span className="text-xs text-gray-400">0</span>
        <span className={`text-xs font-medium ${textColor}`}>
          {pctClamped.toFixed(0)}% utilisé
        </span>
        <span className="text-xs text-gray-400">{docs_quota}</span>
      </div>

      {/* Alerte quota proche */}
      {quota_pct >= 80 && (
        <div
          className={`mt-3 flex items-center gap-2 rounded-lg px-3 py-2 text-xs font-medium
            ${quota_pct >= 90 ? "bg-red-50 text-red-700" : "bg-amber-50 text-amber-700"}`}
        >
          <svg className="w-3.5 h-3.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
          </svg>
          {quota_pct >= 90
            ? "Quota presque épuisé — passez au plan supérieur"
            : "Quota bientôt atteint pour ce mois"}
        </div>
      )}
    </div>
  );
}
