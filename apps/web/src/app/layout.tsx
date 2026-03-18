"use client";
import "./globals.css";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "sonner";
import { useState } from "react";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: { staleTime: 30_000, retry: 1 },
    },
  }));

  return (
    <html lang="fr" suppressHydrationWarning>
      <head>
        <title>AO Copilot — Analyse d&apos;Appels d&apos;Offres BTP</title>
        <meta name="description" content="Analysez vos DCE en 5 minutes avec l'IA" />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        {/*
          Anti-flash dark mode script.
          This is a static string literal (no user input) so dangerouslySetInnerHTML
          is safe here — it only reads localStorage and adds a CSS class.
        */}
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{var t=localStorage.getItem("ao-theme");if(t==="dark"||(t==null&&window.matchMedia("(prefers-color-scheme:dark)").matches)){document.documentElement.classList.add("dark")}}catch(e){}})();`,
          }}
        />
      </head>
      <body className="bg-white dark:bg-slate-950 text-slate-900 dark:text-slate-100">
        <QueryClientProvider client={queryClient}>
          {children}
          <Toaster position="top-right" richColors />
        </QueryClientProvider>
        {/* Bouton flottant support email */}
        <a
          href="mailto:contact@ao-copilot.fr?subject=Besoin d'aide — AO Copilot"
          style={{
            position: "fixed", bottom: "24px", right: "24px", zIndex: 9999,
            display: "flex", alignItems: "center", gap: "8px",
            background: "#1e40af", color: "#fff",
            padding: "10px 16px", borderRadius: "9999px",
            fontSize: "13px", fontWeight: 600,
            boxShadow: "0 4px 14px rgba(30,64,175,0.35)",
            textDecoration: "none", transition: "background 0.2s",
          }}
          onMouseEnter={e => (e.currentTarget.style.background = "#1d3faa")}
          onMouseLeave={e => (e.currentTarget.style.background = "#1e40af")}
        >
          <span style={{ fontSize: "15px" }}>✉️</span>
          Besoin d&apos;aide ?
        </a>
      </body>
    </html>
  );
}
