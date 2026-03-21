import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Tarifs — AO Copilot | Analyse IA d'appels d'offres BTP",
  description:
    "Plans à partir de 0€/mois. Gratuit, Starter (69€), Pro (179€), Europe (299€), Business (499€). Analysez vos DCE BTP avec l'IA.",
  openGraph: {
    title: "Tarifs AO Copilot — Analyse d'appels d'offres par IA",
    description: "Plans transparents à partir de 0€. Essai gratuit, sans engagement.",
    url: "https://aocopilot.fr/pricing",
    siteName: "AO Copilot",
    type: "website",
    locale: "fr_FR",
  },
};

export default function PricingLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
