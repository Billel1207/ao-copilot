import type { Metadata } from "next";
import "./globals.css";
import Providers from "@/components/Providers";
import { JsonLd, organizationSchema, softwareAppSchema, faqSchema } from "@/components/seo/JsonLd";

export const metadata: Metadata = {
  title: "AO Copilot — Analyse d'Appels d'Offres BTP",
  description: "Analysez vos DCE en 5 minutes avec l'IA",
  metadataBase: new URL("https://aocopilot.fr"),
  openGraph: {
    type: "website",
    siteName: "AO Copilot",
    title: "AO Copilot — Analyse d'Appels d'Offres BTP par IA",
    description: "Analysez vos DCE en 5 minutes avec l'IA. Résumé, checklist, scoring Go/No-Go, détection de risques.",
    url: "https://aocopilot.fr",
    locale: "fr_FR",
    images: [
      {
        url: "https://aocopilot.fr/icons/icon-512.png",
        width: 512,
        height: 512,
      },
    ],
  },
  twitter: {
    card: "summary",
    title: "AO Copilot — Analyse DCE par IA",
    description: "Analysez vos appels d'offres BTP en 5 minutes avec l'intelligence artificielle.",
  },
  icons: {
    icon: [
      { url: "/favicon.svg", type: "image/svg+xml" },
      { url: "/favicon.ico", sizes: "32x32" },
    ],
    apple: "/icons/icon-192.png",
  },
  manifest: "/manifest.json",
  other: {
    "theme-color": "#2563EB",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        {/* SEO — JSON-LD structured data */}
        <JsonLd data={organizationSchema} />
        <JsonLd data={softwareAppSchema} />
        <JsonLd data={faqSchema} />
        {/*
          Anti-flash dark mode script.
          This is a static string literal (no user input) so dangerouslySetInnerHTML
          is safe here — it only reads localStorage and adds a CSS class.
        */}
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{var t=localStorage.getItem("ao-theme");if(t==="dark"){document.documentElement.classList.add("dark")}}catch(e){}})();`,
          }}
        />
      </head>
      <body className="bg-white dark:bg-slate-950 text-slate-900 dark:text-slate-100">
        <Providers>
          {children}
        </Providers>
        {/* Bouton flottant support email */}
        <a
          href="mailto:contact@ao-copilot.fr?subject=Besoin d'aide — AO Copilot"
          style={{
            position: "fixed", bottom: "24px", right: "24px", zIndex: 9999,
            display: "flex", alignItems: "center", gap: "8px",
            background: "#1e40af", color: "#fff",
            padding: "12px 18px", borderRadius: "9999px",
            minHeight: "44px", minWidth: "44px",
            fontSize: "13px", fontWeight: 600,
            boxShadow: "0 4px 14px rgba(30,64,175,0.35)",
            textDecoration: "none", transition: "background 0.2s",
          }}
        >
          <span style={{ fontSize: "15px" }}>&#9993;</span>
          Besoin d&apos;aide ?
        </a>
      </body>
    </html>
  );
}
