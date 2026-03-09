"use client";

import { useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { useBillingStore } from "@/stores/billing";
import PlanCards from "@/components/billing/PlanCards";
import UsageBar from "@/components/billing/UsageBar";

export default function BillingPage() {
  const searchParams = useSearchParams();
  const { usage, subscription, isLoading, checkoutPlan, error, fetchBilling, createCheckout, openPortal } =
    useBillingStore();

  const success = searchParams.get("success");
  const canceled = searchParams.get("canceled");

  useEffect(() => {
    fetchBilling();
  }, [fetchBilling]);

  const handleUpgrade = async (planId: string) => {
    await createCheckout(planId as "starter" | "pro");
  };

  if (isLoading && !usage) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-100 rounded w-48" />
          <div className="h-28 bg-gray-100 rounded-xl" />
          <div className="grid grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => <div key={i} className="h-64 bg-gray-100 rounded-2xl" />)}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Abonnement & Facturation</h1>
        <p className="text-gray-500 mt-1">
          Gérez votre plan, consultez votre utilisation et vos factures.
        </p>
      </div>

      {/* Notifications post-checkout */}
      {success && (
        <div className="flex items-center gap-3 bg-green-50 border border-green-200 rounded-xl px-4 py-3">
          <svg className="w-5 h-5 text-green-600 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-sm font-medium text-green-800">
            🎉 Votre abonnement a été activé avec succès !
          </p>
        </div>
      )}

      {canceled && (
        <div className="flex items-center gap-3 bg-amber-50 border border-amber-200 rounded-xl px-4 py-3">
          <svg className="w-5 h-5 text-amber-600 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-sm font-medium text-amber-800">
            Paiement annulé. Votre plan n&apos;a pas changé.
          </p>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Utilisation actuelle */}
      {usage && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="md:col-span-2">
            <UsageBar usage={usage} />
          </div>

          {/* Plan actuel + portail */}
          <div className="bg-white rounded-xl border border-gray-100 p-5 shadow-sm">
            <p className="text-sm font-medium text-gray-500 mb-1">Plan actuel</p>
            <div className="flex items-baseline gap-2 mb-4">
              <span className="text-2xl font-bold text-gray-900">{usage.plan_name}</span>
              <span className={`text-xs font-semibold px-2 py-0.5 rounded-full
                ${usage.plan === "pro" ? "bg-blue-100 text-blue-700" :
                  usage.plan === "starter" ? "bg-indigo-100 text-indigo-700" :
                  "bg-gray-100 text-gray-600"}`}>
                {usage.plan.toUpperCase()}
              </span>
            </div>

            {subscription?.stripe_subscription_id && (
              <button
                onClick={openPortal}
                disabled={isLoading}
                className="w-full text-sm font-medium text-blue-600 hover:text-blue-700 border border-blue-200
                  hover:border-blue-300 rounded-lg py-2 px-3 transition-colors duration-150 disabled:opacity-50"
              >
                Gérer mon abonnement →
              </button>
            )}

            {subscription?.cancel_at_period_end && (
              <p className="text-xs text-red-500 mt-2 text-center">
                Annulé — expire le {subscription.current_period_end
                  ? new Date(subscription.current_period_end).toLocaleDateString("fr-FR")
                  : "..."}
              </p>
            )}
          </div>
        </div>
      )}

      {/* Plans disponibles */}
      {usage && (
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Choisir un plan</h2>
          <PlanCards
            plans={usage.plans_available}
            currentPlan={usage.plan}
            onUpgrade={handleUpgrade}
            isLoading={isLoading}
            checkoutPlan={checkoutPlan}
          />
        </div>
      )}

      {/* Section FAQ rapide */}
      <div className="bg-gray-50 rounded-2xl p-6">
        <h3 className="text-base font-semibold text-gray-800 mb-4">Questions fréquentes</h3>
        <div className="space-y-4">
          {[
            {
              q: "Quand commence mon quota mensuel ?",
              a: "Le quota est remis à zéro le 1er de chaque mois calendaire.",
            },
            {
              q: "Puis-je annuler à tout moment ?",
              a: "Oui, sans engagement. L'accès reste actif jusqu'à la fin de la période en cours.",
            },
            {
              q: "Est-ce que mes données sont supprimées si j'annule ?",
              a: "Non. Vos données sont conservées 30 jours après l'annulation, puis supprimées définitivement.",
            },
          ].map(({ q, a }, i) => (
            <div key={i}>
              <p className="text-sm font-medium text-gray-700">{q}</p>
              <p className="text-sm text-gray-500 mt-0.5">{a}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
