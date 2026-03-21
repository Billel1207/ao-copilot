"use client";

import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ResponsiveContainer, Tooltip,
} from "recharts";

interface GoNoGoRadarProps {
  /** Map dimension name → score 0-100 */
  dimensions: Record<string, number>;
  /** Score global (affiché au centre) */
  score?: number;
}

const DIMENSION_LABELS: Record<string, string> = {
  "Capacité financière": "Finance",
  "Certifications": "Certif.",
  "Références similaires": "Réf.",
  "Charge actuelle": "Charge",
  "Zone géographique": "Géo",
  "Partenariats": "Partenaires",
  "Marge visée": "Marge",
  "Délais": "Délais",
  "Risque technique": "Risque",
};

export function GoNoGoRadar({ dimensions, score }: GoNoGoRadarProps) {
  const data = Object.entries(dimensions).map(([key, value]) => ({
    dimension: DIMENSION_LABELS[key] || key,
    value: Math.min(100, Math.max(0, value)),
    fullName: key,
  }));

  if (data.length === 0) {
    return (
      <p className="text-sm text-slate-400 text-center py-8">
        Aucune dimension Go/No-Go disponible.
      </p>
    );
  }

  const scoreColor = (score ?? 0) >= 70 ? "#059669" : (score ?? 0) >= 50 ? "#D97706" : "#DC2626";

  return (
    <div className="relative">
      {score !== undefined && (
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-10
                        flex flex-col items-center pointer-events-none">
          <span className="text-2xl font-extrabold" style={{ color: scoreColor }}>
            {score}
          </span>
          <span className="text-[10px] text-slate-400 font-medium uppercase tracking-wider">
            /100
          </span>
        </div>
      )}
      <ResponsiveContainer width="100%" height={280}>
        <RadarChart data={data} outerRadius="70%">
          <PolarGrid stroke="#E2E8F0" />
          <PolarAngleAxis
            dataKey="dimension"
            tick={{ fontSize: 11, fill: "#64748B" }}
          />
          <PolarRadiusAxis
            domain={[0, 100]}
            tickCount={5}
            tick={{ fontSize: 9, fill: "#94A3B8" }}
          />
          <Tooltip
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            content={({ payload }: any) => {
              if (!payload?.[0]) return null;
              const d = payload[0].payload;
              return (
                <div className="bg-white border border-slate-200 rounded-lg px-3 py-2 shadow-lg text-xs">
                  <p className="font-semibold text-slate-800">{d.fullName}</p>
                  <p className="text-slate-500">Score : <strong>{d.value}/100</strong></p>
                </div>
              );
            }}
          />
          <Radar
            dataKey="value"
            stroke="#2563EB"
            fill="#2563EB"
            fillOpacity={0.15}
            strokeWidth={2}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
