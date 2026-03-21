"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, XCircle, Loader2, RefreshCw, Activity } from "lucide-react";

interface ServiceStatus {
  name: string;
  status: "ok" | "error" | "loading";
  detail?: string;
  latency?: number;
}

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace("/api/v1", "") || "http://localhost:8000";

/**
 * Public health check page — /status
 *
 * No auth required. Useful for:
 * - Monitoring tools (UptimeRobot, Pingdom, etc.)
 * - Customer support to check service status
 * - Quick debugging during incidents
 */
export default function StatusPage() {
  const [services, setServices] = useState<ServiceStatus[]>([
    { name: "Frontend", status: "loading" },
    { name: "API", status: "loading" },
    { name: "Base de données", status: "loading" },
    { name: "Redis (File d'attente)", status: "loading" },
  ]);
  const [lastCheck, setLastCheck] = useState<Date | null>(null);
  const [checking, setChecking] = useState(false);

  const checkHealth = async () => {
    setChecking(true);

    // Frontend is always OK if this page renders
    const updated: ServiceStatus[] = [
      { name: "Frontend", status: "ok", detail: "Next.js", latency: 0 },
    ];

    try {
      const start = performance.now();
      const res = await fetch(`${API_BASE}/api/health/ready`, {
        signal: AbortSignal.timeout(10_000),
      });
      const latency = Math.round(performance.now() - start);
      const data = await res.json();

      updated.push({
        name: "API",
        status: data.status === "ok" || data.status === "degraded" ? "ok" : "error",
        detail: `v${data.version ?? "?"}`,
        latency,
      });
      updated.push({
        name: "Base de données",
        status: data.database === "ok" ? "ok" : "error",
        detail: data.database === "ok" ? "PostgreSQL" : data.database,
      });
      updated.push({
        name: "Redis (File d'attente)",
        status: data.redis === "ok" ? "ok" : "error",
        detail: data.redis === "ok" ? "Celery broker" : data.redis,
      });
    } catch {
      updated.push(
        { name: "API", status: "error", detail: "Injoignable" },
        { name: "Base de données", status: "error", detail: "Inconnu" },
        { name: "Redis (File d'attente)", status: "error", detail: "Inconnu" },
      );
    }

    setServices(updated);
    setLastCheck(new Date());
    setChecking(false);
  };

  useEffect(() => {
    checkHealth();
    // Auto-refresh every 30s
    const interval = setInterval(checkHealth, 30_000);
    return () => clearInterval(interval);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const allOk = services.every((s) => s.status === "ok");
  const anyError = services.some((s) => s.status === "error");

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex items-center justify-center p-6">
      <div className="w-full max-w-lg">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-2 mb-3">
            <div className="w-8 h-8 bg-gradient-to-br from-primary-700 to-primary-900 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">AO</span>
            </div>
            <span className="font-bold text-primary-900 dark:text-white text-lg">AO Copilot</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-1">
            État des services
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Vérification en temps réel de l&apos;infrastructure
          </p>
        </div>

        {/* Global status banner */}
        <div
          className={`rounded-2xl p-5 mb-6 border ${
            allOk
              ? "bg-emerald-50 dark:bg-emerald-900/20 border-emerald-200 dark:border-emerald-800"
              : anyError
                ? "bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800"
                : "bg-slate-100 dark:bg-slate-800 border-slate-200 dark:border-slate-700"
          }`}
        >
          <div className="flex items-center gap-3">
            {services.some((s) => s.status === "loading") ? (
              <Loader2 className="w-6 h-6 text-slate-400 animate-spin" />
            ) : allOk ? (
              <CheckCircle2 className="w-6 h-6 text-emerald-600 dark:text-emerald-400" />
            ) : (
              <XCircle className="w-6 h-6 text-red-600 dark:text-red-400" />
            )}
            <div>
              <p className="font-semibold text-slate-900 dark:text-white">
                {services.some((s) => s.status === "loading")
                  ? "Vérification en cours…"
                  : allOk
                    ? "Tous les services sont opérationnels"
                    : "Certains services rencontrent des problèmes"}
              </p>
              {lastCheck && (
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                  Dernière vérification : {lastCheck.toLocaleTimeString("fr-FR")}
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Service list */}
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 divide-y divide-slate-100 dark:divide-slate-800 shadow-sm">
          {services.map((service) => (
            <div
              key={service.name}
              className="flex items-center justify-between px-5 py-4"
            >
              <div className="flex items-center gap-3">
                <Activity className="w-4 h-4 text-slate-400 dark:text-slate-500" />
                <div>
                  <p className="text-sm font-medium text-slate-800 dark:text-slate-200">
                    {service.name}
                  </p>
                  {service.detail && (
                    <p className="text-xs text-slate-400 dark:text-slate-500">
                      {service.detail}
                    </p>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-2">
                {service.latency !== undefined && service.latency > 0 && (
                  <span className="text-xs text-slate-400">{service.latency}ms</span>
                )}
                {service.status === "loading" ? (
                  <Loader2 className="w-4 h-4 text-slate-300 animate-spin" />
                ) : service.status === "ok" ? (
                  <span className="flex items-center gap-1 text-xs font-medium text-emerald-600 dark:text-emerald-400">
                    <span className="w-2 h-2 bg-emerald-500 rounded-full" />
                    OK
                  </span>
                ) : (
                  <span className="flex items-center gap-1 text-xs font-medium text-red-600 dark:text-red-400">
                    <span className="w-2 h-2 bg-red-500 rounded-full" />
                    Erreur
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Refresh button */}
        <div className="flex justify-center mt-6">
          <button
            onClick={checkHealth}
            disabled={checking}
            className="flex items-center gap-2 px-4 py-2.5 min-h-[44px] text-sm font-medium
                       text-slate-600 dark:text-slate-300 bg-white dark:bg-slate-900
                       border border-slate-200 dark:border-slate-700 rounded-xl
                       hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors
                       disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${checking ? "animate-spin" : ""}`} />
            Rafraîchir
          </button>
        </div>

        {/* Footer */}
        <p className="text-center text-xs text-slate-400 dark:text-slate-500 mt-6">
          Hébergé en France 🇫🇷 · Actualisation automatique toutes les 30s
        </p>
      </div>
    </div>
  );
}
