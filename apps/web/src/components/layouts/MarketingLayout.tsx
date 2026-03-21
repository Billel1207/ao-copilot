import Link from "next/link";

export default function MarketingLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-white">
      {/* Skip link (WCAG 2.1 A) */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-[100]
                   focus:bg-blue-600 focus:text-white focus:px-4 focus:py-2 focus:rounded-lg
                   focus:text-sm focus:font-semibold focus:shadow-lg"
      >
        Aller au contenu principal
      </a>
      <header className="border-b px-6 py-4 flex items-center justify-between">
        <Link href="/" className="font-bold text-blue-700 text-lg">AO Copilot</Link>
        <Link href="/" className="text-sm text-gray-500 hover:text-gray-900">← Retour à l&apos;accueil</Link>
      </header>
      <main id="main-content" tabIndex={-1}>{children}</main>
      <footer className="border-t px-6 py-4 text-center text-xs text-gray-400">
        © 2026 AO Copilot —{" "}
        <Link href="/legal/mentions-legales" className="hover:underline">Mentions légales</Link>
        {" · "}
        <Link href="/legal/cgu" className="hover:underline">CGU</Link>
        {" · "}
        <Link href="/legal/confidentialite" className="hover:underline">Confidentialité</Link>
        {" · "}
        <Link href="/legal/ai-transparency" className="hover:underline">Transparence IA</Link>
      </footer>
    </div>
  );
}
