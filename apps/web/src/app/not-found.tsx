import Link from "next/link";

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-950 dark:to-slate-900 px-6">
      <div className="text-center max-w-md">
        {/* Illustration 404 */}
        <div className="mb-8">
          <span className="text-8xl font-extrabold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
            404
          </span>
        </div>

        <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-3">
          Page introuvable
        </h1>

        <p className="text-slate-600 dark:text-slate-400 mb-8 leading-relaxed">
          La page que vous recherchez n&apos;existe pas ou a été déplacée.
          Vérifiez l&apos;URL ou retournez au tableau de bord.
        </p>

        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link
            href="/dashboard"
            className="inline-flex items-center justify-center px-6 py-3 rounded-lg bg-blue-600 text-white font-medium hover:bg-blue-700 transition-colors"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-4 0a1 1 0 01-1-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 01-1 1" />
            </svg>
            Tableau de bord
          </Link>

          <Link
            href="/"
            className="inline-flex items-center justify-center px-6 py-3 rounded-lg border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 font-medium hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            Accueil
          </Link>
        </div>

        <p className="mt-10 text-xs text-slate-400 dark:text-slate-500">
          Besoin d&apos;aide ?{" "}
          <a href="mailto:contact@ao-copilot.fr" className="text-blue-500 hover:underline">
            contact@ao-copilot.fr
          </a>
        </p>
      </div>
    </div>
  );
}
