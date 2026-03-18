"use client";

import * as Sentry from "@sentry/nextjs";
import { useEffect } from "react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    Sentry.captureException(error);
  }, [error]);

  return (
    <html lang="fr">
      <body>
        <div style={{
          display: "flex", minHeight: "100vh", flexDirection: "column",
          alignItems: "center", justifyContent: "center", padding: "1rem",
          fontFamily: "system-ui, sans-serif", textAlign: "center",
        }}>
          <div style={{
            border: "1px solid #fecaca", backgroundColor: "#fef2f2",
            borderRadius: "12px", padding: "2rem", maxWidth: "400px",
          }}>
            <h2 style={{ color: "#991b1b", fontSize: "1.125rem", fontWeight: 600, marginBottom: "0.5rem" }}>
              Erreur critique
            </h2>
            <p style={{ color: "#dc2626", fontSize: "0.875rem", marginBottom: "1rem" }}>
              L&apos;application a rencontr&eacute; une erreur critique.
            </p>
            <button
              onClick={reset}
              style={{
                backgroundColor: "#dc2626", color: "#fff", border: "none",
                borderRadius: "8px", padding: "0.5rem 1rem",
                fontSize: "0.875rem", fontWeight: 500, cursor: "pointer",
              }}
            >
              Recharger
            </button>
          </div>
        </div>
      </body>
    </html>
  );
}
