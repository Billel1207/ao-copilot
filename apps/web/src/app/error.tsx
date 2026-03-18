"use client";

import * as Sentry from "@sentry/nextjs";
import { useEffect } from "react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    Sentry.captureException(error);
    console.error("Application error:", error);
  }, [error]);

  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center px-4 text-center">
      <div className="rounded-xl border border-red-200 bg-red-50 p-8 max-w-md">
        <h2 className="text-lg font-semibold text-red-800 mb-2">
          Une erreur est survenue
        </h2>
        <p className="text-sm text-red-600 mb-4">
          L&apos;application a rencontré un problème inattendu. Veuillez réessayer.
        </p>
        <button
          onClick={reset}
          className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 transition-colors"
        >
          Recharger la page
        </button>
      </div>
    </div>
  );
}
