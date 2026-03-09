"use client";

import { PlanInfo } from "@/stores/billing";

interface PlanCardsProps {
  plans: PlanInfo[];
  currentPlan: string;
  onUpgrade: (planId: string) => void;
  isLoading?: boolean;
  /** Plan en cours de checkout — seul ce bouton se grise */
  checkoutPlan?: "starter" | "pro" | "europe" | null;
}

const PLAN_HIGHLIGHTS: Record<string, { badge?: string; borderClass: string; btnClass: string }> = {
  free: {
    borderClass: "border-gray-200",
    btnClass: "bg-gray-100 text-gray-500 cursor-not-allowed",
  },
  starter: {
    borderClass: "border-blue-200",
    btnClass: "bg-blue-600 hover:bg-blue-700 text-white",
  },
  pro: {
    badge: "Recommandé",
    borderClass: "border-blue-600 ring-2 ring-blue-600/20",
    btnClass: "bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white shadow-md",
  },
  europe: {
    badge: "Expansion UE",
    borderClass: "border-purple-500 ring-2 ring-purple-500/20",
    btnClass: "bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white shadow-md",
  },
};

const PLAN_ICONS: Record<string, string> = {
  free: "🎯",
  starter: "🚀",
  pro: "⚡",
  europe: "🌍",
};

export default function PlanCards({
  plans,
  currentPlan,
  onUpgrade,
  isLoading = false,
  checkoutPlan = null,
}: PlanCardsProps) {
  // Grille adaptative : 3 cols pour ≤3 plans, 4 cols pour 4 plans (ex: avec Europe)
  const gridCols =
    plans.length >= 4
      ? "grid-cols-1 sm:grid-cols-2 lg:grid-cols-4"
      : "grid-cols-1 md:grid-cols-3";

  return (
    <div className={`grid ${gridCols} gap-4`}>
      {plans.map((plan) => {
        const highlight = PLAN_HIGHLIGHTS[plan.id] ?? {
          borderClass: "border-gray-200",
          btnClass: "bg-blue-600 hover:bg-blue-700 text-white",
        };
        const isCurrent = plan.id === currentPlan;
        const isUpgrade = plan.id !== "free" && plan.id !== currentPlan;
        // Ce plan est-il en cours de paiement ? (seul lui se grise)
        const isPlanLoading = checkoutPlan === plan.id || (isLoading && plan.id === currentPlan);

        return (
          <div
            key={plan.id}
            className={`relative flex flex-col rounded-2xl border-2 bg-white p-6 shadow-sm
              transition-shadow hover:shadow-md ${highlight.borderClass}
              ${plan.id === "pro" || plan.id === "europe" ? "scale-[1.02]" : ""}`}
          >
            {/* Badge recommandé / Expansion UE */}
            {highlight.badge && (
              <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                <span
                  className={`text-white text-xs font-semibold px-3 py-1 rounded-full shadow-sm ${
                    plan.id === "europe"
                      ? "bg-gradient-to-r from-purple-600 to-indigo-600"
                      : "bg-blue-600"
                  }`}
                >
                  {highlight.badge}
                </span>
              </div>
            )}

            {/* Plan header */}
            <div className="mb-4">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-2xl">{PLAN_ICONS[plan.id] ?? "📦"}</span>
                <h3 className="text-lg font-bold text-gray-900">{plan.name}</h3>
                {isCurrent && (
                  <span className="ml-auto bg-green-100 text-green-700 text-xs font-semibold px-2 py-0.5 rounded-full">
                    Actuel
                  </span>
                )}
              </div>

              {/* Prix */}
              <div className="flex items-baseline gap-1">
                {plan.monthly_eur > 0 ? (
                  <>
                    <span className="text-3xl font-extrabold text-gray-900">
                      {plan.monthly_eur.toFixed(0)}€
                    </span>
                    <span className="text-gray-400 text-sm">/mois HT</span>
                  </>
                ) : (
                  <span className="text-3xl font-extrabold text-gray-900">Gratuit</span>
                )}
              </div>
            </div>

            {/* Specs */}
            <div className="flex flex-col gap-2 mb-5 flex-1">
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <svg className="w-4 h-4 text-blue-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <span><strong>{plan.docs_per_month === 999 ? "Illimité" : plan.docs_per_month}</strong> documents/mois</span>
              </div>

              <div className="flex items-center gap-2 text-sm text-gray-600">
                <svg className="w-4 h-4 text-blue-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                <span><strong>{plan.max_users === 999 ? "Illimité" : plan.max_users}</strong> utilisateur{plan.max_users > 1 ? "s" : ""}</span>
              </div>

              {plan.word_export && (
                <div className="flex items-center gap-2 text-sm text-green-600">
                  <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span className="font-medium">Export Word inclus</span>
                </div>
              )}

              {/* Features list */}
              <ul className="mt-2 space-y-1.5">
                {plan.features.slice(2).map((feat, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-gray-500">
                    <svg className="w-3.5 h-3.5 text-green-500 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                    {feat}
                  </li>
                ))}
              </ul>
            </div>

            {/* CTA Button */}
            <button
              onClick={() => isUpgrade && !checkoutPlan && onUpgrade(plan.id)}
              disabled={isCurrent || plan.id === "free" || !!checkoutPlan}
              className={`w-full py-2.5 px-4 rounded-xl text-sm font-semibold transition-all duration-200
                disabled:cursor-not-allowed
                ${isCurrent
                  ? "bg-gray-100 text-gray-400 cursor-not-allowed opacity-50"
                  : isPlanLoading
                    ? `${highlight.btnClass} opacity-70`
                    : checkoutPlan && !isCurrent
                      ? `${highlight.btnClass} opacity-40`
                      : highlight.btnClass
                }`}
            >
              {isPlanLoading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Redirection Stripe...
                </span>
              ) : isCurrent ? (
                "Plan actuel"
              ) : plan.id === "free" ? (
                "Plan gratuit"
              ) : (
                `Passer au ${plan.name}`
              )}
            </button>

            {/* Moyens de paiement acceptés */}
            {plan.id !== "free" && (
              <div className="mt-3 pt-3 border-t border-gray-100">
                <p className="text-[10px] text-gray-400 text-center mb-1.5">Paiement sécurisé via Stripe</p>
                <div className="flex items-center justify-center gap-1 flex-wrap">
                  {[
                    { label: "CB", title: "Carte bancaire" },
                    { label: "SEPA", title: "Virement SEPA" },
                    { label: "Apple Pay", title: "Apple Pay" },
                    { label: "Google Pay", title: "Google Pay" },
                    { label: "PayPal", title: "PayPal" },
                  ].map((m) => (
                    <span
                      key={m.label}
                      title={m.title}
                      className="text-[10px] bg-slate-100 hover:bg-slate-200 px-1.5 py-0.5 rounded font-medium text-slate-500 transition-colors"
                    >
                      {m.label}
                    </span>
                  ))}
                </div>
                <div className="flex items-center justify-center gap-1 mt-1.5">
                  <svg className="w-3 h-3 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                  <span className="text-[10px] text-green-600 font-medium">Crypté SSL · 3D Secure</span>
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
