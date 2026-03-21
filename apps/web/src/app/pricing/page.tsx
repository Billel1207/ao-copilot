"use client";

import Link from "next/link";
import { useState } from "react";

const plans = [
  {
    name: "Gratuit",
    price: 0,
    priceAnnual: 0,
    description: "Pour découvrir AO Copilot",
    features: [
      "2 documents / mois",
      "1 utilisateur",
      "Analyse IA basique",
      "14 jours de rétention",
    ],
    cta: "Commencer gratuitement",
    href: "/register",
    popular: false,
  },
  {
    name: "Starter",
    price: 69,
    priceAnnual: 55,
    description: "Pour les indépendants et petites structures",
    features: [
      "15 documents / mois",
      "1 utilisateur",
      "Analyse IA complète",
      "Export Word",
      "30 jours de rétention",
    ],
    cta: "Essayer Starter",
    href: "/register?plan=starter",
    popular: false,
  },
  {
    name: "Pro",
    price: 179,
    priceAnnual: 143,
    description: "Pour les PME et bureaux d\u2019études",
    features: [
      "60 documents / mois",
      "5 utilisateurs",
      "Analyse IA avancée",
      "Export Word + Excel",
      "90 jours de rétention",
      "Support prioritaire",
    ],
    cta: "Choisir Pro",
    href: "/register?plan=pro",
    popular: true,
  },
  {
    name: "Europe",
    price: 299,
    priceAnnual: 239,
    description: "Pour les marchés européens (TED, Wallonie, Luxembourg)",
    features: [
      "100 documents / mois",
      "20 utilisateurs",
      "Veille TED automatique",
      "Analyse multilingue",
      "180 jours de rétention",
      "Support dédié",
    ],
    cta: "Passer à Europe",
    href: "/register?plan=europe",
    popular: false,
  },
  {
    name: "Business",
    price: 499,
    priceAnnual: 399,
    description: "Pour les grands groupes BTP",
    features: [
      "Documents illimités",
      "Utilisateurs illimités",
      "SSO SAML",
      "API & Webhooks",
      "SLA 99.9%",
      "Account manager dédié",
    ],
    cta: "Contacter les ventes",
    href: "mailto:contact@ao-copilot.fr?subject=Plan Business",
    popular: false,
  },
];

export default function PricingPage() {
  const [annual, setAnnual] = useState(false);

  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-slate-50 dark:from-slate-950 dark:to-slate-900">
      {/* Header */}
      <header className="border-b border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-950/80 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/" className="text-xl font-bold text-blue-600">
            AO Copilot
          </Link>
          <Link
            href="/login"
            className="text-sm font-medium text-slate-600 dark:text-slate-400 hover:text-blue-600"
          >
            Se connecter
          </Link>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-16">
        {/* Title */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-extrabold text-slate-900 dark:text-white mb-4">
            Des tarifs simples et transparents
          </h1>
          <p className="text-lg text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">
            Choisissez le plan adapté à votre volume d&apos;appels d&apos;offres.
            Tous les plans incluent l&apos;analyse IA et le support.
          </p>

          {/* Toggle Annual/Monthly */}
          <div className="mt-8 flex items-center justify-center gap-3">
            <span className={`text-sm font-medium ${!annual ? "text-slate-900 dark:text-white" : "text-slate-500"}`}>
              Mensuel
            </span>
            <button
              onClick={() => setAnnual(!annual)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                annual ? "bg-blue-600" : "bg-slate-300 dark:bg-slate-600"
              }`}
              role="switch"
              aria-checked={annual}
              aria-label="Basculer entre facturation mensuelle et annuelle"
            >
              <span
                className={`inline-block h-4 w-4 rounded-full bg-white transition-transform ${
                  annual ? "translate-x-6" : "translate-x-1"
                }`}
              />
            </button>
            <span className={`text-sm font-medium ${annual ? "text-slate-900 dark:text-white" : "text-slate-500"}`}>
              Annuel
            </span>
            {annual && (
              <span className="ml-1 text-xs font-semibold text-green-600 bg-green-50 dark:bg-green-900/30 dark:text-green-400 px-2 py-0.5 rounded-full">
                -20%
              </span>
            )}
          </div>
        </div>

        {/* Plans Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6">
          {plans.map((plan) => {
            const price = annual ? plan.priceAnnual : plan.price;
            return (
              <div
                key={plan.name}
                className={`relative bg-white dark:bg-slate-900 rounded-2xl p-6 shadow-sm border transition-shadow hover:shadow-md ${
                  plan.popular
                    ? "border-blue-500 ring-2 ring-blue-500/20"
                    : "border-slate-200 dark:border-slate-700"
                }`}
              >
                {plan.popular && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <span className="bg-blue-600 text-white text-xs font-bold px-3 py-1 rounded-full">
                      Recommandé
                    </span>
                  </div>
                )}

                <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-1">
                  {plan.name}
                </h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">
                  {plan.description}
                </p>

                <div className="mb-6">
                  <span className="text-3xl font-extrabold text-slate-900 dark:text-white">
                    {price === 0 ? "0" : `${price}`}
                  </span>
                  <span className="text-slate-500 dark:text-slate-400 text-sm ml-1">
                    {price === 0 ? "€" : "€/mois"}
                  </span>
                </div>

                <ul className="space-y-2 mb-6">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-start gap-2 text-sm text-slate-600 dark:text-slate-400">
                      <svg className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      {feature}
                    </li>
                  ))}
                </ul>

                <Link
                  href={plan.href}
                  className={`block text-center py-2.5 px-4 rounded-lg text-sm font-semibold transition-colors ${
                    plan.popular
                      ? "bg-blue-600 text-white hover:bg-blue-700"
                      : "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700"
                  }`}
                >
                  {plan.cta}
                </Link>
              </div>
            );
          })}
        </div>

        {/* Pay-per-doc */}
        <div className="mt-12 text-center">
          <p className="text-slate-600 dark:text-slate-400">
            Besoin ponctuel ?{" "}
            <span className="font-semibold text-slate-900 dark:text-white">3 €/document</span>{" "}
            en achat unitaire, sans abonnement.
          </p>
        </div>
      </div>
    </div>
  );
}
