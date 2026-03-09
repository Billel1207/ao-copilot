import Link from "next/link";

export default function MarketingLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-white">
      <header className="border-b px-6 py-4 flex items-center justify-between">
        <Link href="/" className="font-bold text-blue-700 text-lg">AO Copilot</Link>
        <Link href="/" className="text-sm text-gray-500 hover:text-gray-900">← Retour à l&apos;accueil</Link>
      </header>
      <main>{children}</main>
      <footer className="border-t px-6 py-4 text-center text-xs text-gray-400">
        © 2026 AO Copilot —{" "}
        <Link href="/legal/mentions-legales" className="hover:underline">Mentions légales</Link>
        {" · "}
        <Link href="/legal/cgu" className="hover:underline">CGU</Link>
        {" · "}
        <Link href="/legal/confidentialite" className="hover:underline">Confidentialité</Link>
      </footer>
    </div>
  );
}
