/**
 * JSON-LD structured data component for SEO.
 *
 * Renders a <script type="application/ld+json"> tag with the provided data.
 * Use on marketing/public pages to improve Google rich snippet display.
 *
 * Security note: The data object is a static, hardcoded schema defined in this
 * file — no user input is ever interpolated. JSON.stringify safely escapes all
 * values. This is the standard Next.js pattern for JSON-LD.
 */
export function JsonLd({ data }: { data: Record<string, unknown> }) {
  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(data) }}
    />
  );
}

/** Organization schema for AO Copilot. */
export const organizationSchema = {
  "@context": "https://schema.org",
  "@type": "Organization",
  name: "AO Copilot",
  url: "https://aocopilot.fr",
  logo: "https://aocopilot.fr/icons/icon-512.png",
  description:
    "Plateforme SaaS d'analyse automatique des appels d'offres BTP par intelligence artificielle.",
  foundingDate: "2026",
  address: {
    "@type": "PostalAddress",
    addressLocality: "Paris",
    addressCountry: "FR",
  },
  contactPoint: {
    "@type": "ContactPoint",
    email: "contact@aocopilot.fr",
    contactType: "customer support",
    availableLanguage: "French",
  },
};

/** SoftwareApplication schema. */
export const softwareAppSchema = {
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  name: "AO Copilot",
  applicationCategory: "BusinessApplication",
  operatingSystem: "Web",
  url: "https://aocopilot.fr",
  description:
    "Analysez vos DCE (Dossiers de Consultation des Entreprises) en 5 minutes avec l'IA. Résumé, checklist, scoring Go/No-Go, détection de risques.",
  offers: [
    {
      "@type": "Offer",
      name: "Gratuit",
      price: "0",
      priceCurrency: "EUR",
      description: "2 documents / mois, 1 utilisateur",
    },
    {
      "@type": "Offer",
      name: "Starter",
      price: "69",
      priceCurrency: "EUR",
      description: "15 documents / mois, analyse IA complète, export Word",
    },
    {
      "@type": "Offer",
      name: "Pro",
      price: "179",
      priceCurrency: "EUR",
      description: "60 documents / mois, 5 utilisateurs, support prioritaire",
    },
    {
      "@type": "Offer",
      name: "Business",
      price: "499",
      priceCurrency: "EUR",
      description: "Documents illimités, SSO SAML, SLA 99.9%",
    },
  ],
};

/** FAQ schema — displayed as rich snippets in Google SERPs. */
export const faqSchema = {
  "@context": "https://schema.org",
  "@type": "FAQPage",
  mainEntity: [
    {
      "@type": "Question",
      name: "Qu'est-ce qu'AO Copilot ?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "AO Copilot est une plateforme SaaS qui utilise l'intelligence artificielle pour analyser automatiquement les Dossiers de Consultation des Entreprises (DCE) dans le secteur du BTP. Elle génère des résumés, checklists, scores Go/No-Go et détecte les risques en quelques minutes.",
      },
    },
    {
      "@type": "Question",
      name: "Combien coûte AO Copilot ?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "AO Copilot propose un plan gratuit (2 documents/mois), un plan Starter à 69€/mois, un plan Pro à 179€/mois, un plan Europe à 299€/mois et un plan Business à 499€/mois. Une réduction de 20% est appliquée sur la facturation annuelle.",
      },
    },
    {
      "@type": "Question",
      name: "Quels types de documents sont analysés ?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "AO Copilot analyse les documents PDF du DCE : Règlement de Consultation (RC), CCAP, CCTP, DPGF/BPU, Acte d'Engagement, et autres pièces administratives. L'OCR intégré permet de traiter les documents scannés.",
      },
    },
    {
      "@type": "Question",
      name: "Mes données sont-elles sécurisées ?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "Oui. Les documents sont stockés en France (Paris) sur Scaleway Object Storage, conforme au RGPD. Les accès sont sécurisés par des liens signés à durée limitée (15 minutes). Vos documents ne sont jamais utilisés pour entraîner les modèles d'IA.",
      },
    },
    {
      "@type": "Question",
      name: "Comment fonctionne l'analyse IA ?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "AO Copilot utilise Claude (Anthropic) pour analyser le contenu de vos documents DCE. L'IA extrait les informations clés, identifie les risques contractuels, vérifie les délais et critères d'éligibilité, et génère un score Go/No-Go stratégique.",
      },
    },
  ],
};

export default JsonLd;
