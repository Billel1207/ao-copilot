"use client";

import * as Sentry from "@sentry/nextjs";
import { useEffect } from "react";
import Link from "next/link";

/**
 * Auth-specific error boundary.
 * Clean, minimal error UI matching the auth pages' style.
 */
export default function AuthError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    Sentry.captureException(error, { tags: { segment: "auth" } });
    console.error("[Auth Error]", error);
  }, [error]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-950 dark:to-slate-900 px-4">
      <div className="max-w-sm w-full text-center">
        <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-blue-800 rounded-xl flex items-center justify-center mx-auto mb-6">
          <span className="text-white font-bold text-lg">AO</span>
        </div>
        <h2 className="text-lg font-bold text-slate-800 dark:text-white mb-2">
          Erreur de connexion
        </h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mb-6">
          Un problème technique est survenu. Veuillez réessayer dans quelques instants.
        </p>
        <div className="flex flex-col gap-3">
          <button
            onClick={reset}
            className="w-full py-3 min-h-[44px] bg-blue-600 text-white rounded-xl text-sm font-semibold hover:bg-blue-700 transition-colors"
          >
            Réessayer
          </button>
          <Link
            href="/"
            className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
          >
            Retour à l&apos;accueil
          </Link>
        </div>
      </div>
    </div>
  );
}
