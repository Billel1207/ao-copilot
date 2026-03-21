"use client";

import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine,
} from "recharts";

interface CashflowChartProps {
  /** Trésorerie cumulée par mois */
  monthlyCashflow: number[];
  /** Seuil BFR (ligne de référence) */
  bfrPeak?: number;
  /** Budget total du marché */
  totalBudget?: number;
}

export function CashflowChart({ monthlyCashflow, bfrPeak, totalBudget }: CashflowChartProps) {
  if (!monthlyCashflow || monthlyCashflow.length === 0) {
    return <p className="text-sm text-slate-400 text-center py-8">Aucune donnée de trésorerie.</p>;
  }

  const data = monthlyCashflow.map((val, i) => ({
    month: `M${i + 1}`,
    value: val,
    isNegative: val < 0,
  }));

  const minVal = Math.min(0, ...monthlyCashflow);
  const maxVal = Math.max(...monthlyCashflow);

  const formatEur = (v: number) => {
    if (Math.abs(v) >= 1_000_000) return `${(v / 1_000_000).toFixed(1)}M`;
    if (Math.abs(v) >= 1000) return `${(v / 1000).toFixed(0)}K`;
    return `${v}`;
  };

  return (
    <div>
      <ResponsiveContainer width="100%" height={220}>
        <AreaChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
          <defs>
            <linearGradient id="cashflowGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#059669" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#059669" stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
          <XAxis dataKey="month" tick={{ fontSize: 11, fill: "#94A3B8" }} />
          <YAxis
            tickFormatter={formatEur}
            tick={{ fontSize: 10, fill: "#94A3B8" }}
            domain={[minVal * 1.1, maxVal * 1.1]}
          />
          <Tooltip
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            content={({ payload }: any) => {
              if (!payload?.[0]) return null;
              const d = payload[0].payload;
              return (
                <div className="bg-white border border-slate-200 rounded-lg px-3 py-2 shadow-lg text-xs">
                  <p className="font-semibold text-slate-800">{d.month}</p>
                  <p className="text-slate-500">
                    Trésorerie : <strong>{formatEur(d.value)} EUR</strong>
                  </p>
                </div>
              );
            }}
          />
          <ReferenceLine y={0} stroke="#94A3B8" strokeDasharray="3 3" />
          {bfrPeak !== undefined && bfrPeak < 0 && (
            <ReferenceLine
              y={bfrPeak}
              stroke="#DC2626"
              strokeDasharray="5 5"
              label={{ value: "BFR pic", fill: "#DC2626", fontSize: 10 }}
            />
          )}
          <Area
            type="monotone"
            dataKey="value"
            stroke="#059669"
            strokeWidth={2}
            fill="url(#cashflowGrad)"
          />
        </AreaChart>
      </ResponsiveContainer>
      {totalBudget !== undefined && (
        <p className="text-center text-xs text-slate-400 mt-2">
          Budget total : <strong>{formatEur(totalBudget)} EUR</strong>
        </p>
      )}
    </div>
  );
}
