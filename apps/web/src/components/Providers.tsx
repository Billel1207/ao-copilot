"use client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "sonner";
import { useEffect, useState } from "react";

export default function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: { staleTime: 30_000, retry: 1 },
    },
  }));

  // Register Service Worker for PWA offline support
  useEffect(() => {
    if ("serviceWorker" in navigator && process.env.NODE_ENV === "production") {
      navigator.serviceWorker.register("/sw.js").catch(() => {
        // SW registration failed — non-critical, app works without it
      });
    }

    // ── ChunkLoadError auto-recovery ──────────────────────────────────
    // After a redeploy, old cached manifests may reference chunks with
    // stale hashes that no longer exist on the server. This causes a
    // ChunkLoadError that crashes React hydration → white screen.
    // Solution: catch the error globally and force a single hard reload.
    const handleChunkError = (event: ErrorEvent) => {
      if (
        event.message?.includes("ChunkLoadError") ||
        event.message?.includes("Loading chunk") ||
        event.message?.includes("Failed to fetch dynamically imported module")
      ) {
        // Prevent infinite reload loop — only reload once per session
        const reloadKey = "ao-chunk-reload";
        if (!sessionStorage.getItem(reloadKey)) {
          sessionStorage.setItem(reloadKey, "1");
          // Clear SW cache before reloading
          if ("caches" in window) {
            caches.keys().then((names) => {
              names.forEach((name) => caches.delete(name));
            });
          }
          window.location.reload();
        }
      }
    };
    window.addEventListener("error", handleChunkError);
    return () => window.removeEventListener("error", handleChunkError);
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <Toaster position="top-right" richColors />
    </QueryClientProvider>
  );
}
