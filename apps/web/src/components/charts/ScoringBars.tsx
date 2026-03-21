"use client";

import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, LabelList,
} from "recharts";

interface Criterion {
  name: string;
  weight: number;
  estimated_score?: number;
  weighted_score?: number;
}

interface ScoringBarsProps {
  criteria: Criterion[];
  totalWeighted?: number;
}

const COLORS = ["#2563EB", "#7C3AED", "#059669", "#D97706", "#DC2626", "#0891B2"];

export function ScoringBars({ criteria, totalWeighted }: ScoringBarsProps) {
  if (!criteria || criteria.length === 0) {
    return <p className="text-sm text-slate-400 text-center py-8">Aucun critère de scoring.</p>;
  }

  const data = criteria.map((c, i) => ({
    name: c.name,
    score: c.estimated_score ?? 0,
    weighted: c.weighted_score ?? ((c.estimated_score ?? 0) * c.weight / 100),
    weight: c.weight,
    color: COLORS[i % COLORS.length],
  }));

  return (
    <div>
      <ResponsiveContainer width="100%" height={Math.max(180, criteria.length * 50)}>
        <BarChart data={data} layout="vertical" margin={{ left: 10, right: 30 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" horizontal={false} />
          <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 10, fill: "#94A3B8" }} />
          <YAxis
            dataKey="name"
            type="category"
            width={100}
            tick={{ fontSize: 11, fill: "#475569" }}
          />
          <Tooltip
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            content={({ payload }: any) => {
              if (!payload?.[0]) return null;
              const d = payload[0].payload;
              return (
                <div className="bg-white border border-slate-200 rounded-lg px-3 py-2 shadow-lg text-xs">
                  <p className="font-semibold text-slate-800">{d.name}</p>
                  <p className="text-slate-500">
                    Score : {d.score}/100 (poids {d.weight}%)
                  </p>
                  <p className="text-slate-500">
                    Score pondéré : <strong>{d.weighted.toFixed(1)}</strong>
                  </p>
                </div>
              );
            }}
          />
          <Bar dataKey="score" radius={[0, 6, 6, 0]} barSize={24}>
            {data.map((entry, idx) => (
              <Cell key={idx} fill={entry.color} />
            ))}
            <LabelList
              dataKey="score"
              position="right"
              formatter={(v: number) => `${v}`}
              style={{ fontSize: 11, fill: "#475569", fontWeight: 600 }}
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      {totalWeighted !== undefined && (
        <div className="mt-3 text-center">
          <span className="text-xs text-slate-400">Score global pondéré : </span>
          <span className="text-lg font-bold text-slate-800">{totalWeighted.toFixed(1)}</span>
          <span className="text-xs text-slate-400">/100</span>
        </div>
      )}
    </div>
  );
}
