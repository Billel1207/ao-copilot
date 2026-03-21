/**
 * AO Copilot — Service Worker (PWA offline support)
 *
 * Strategy:
 * - /_next/static/ JS/CSS chunks: Network-first with cache fallback
 *   (NEVER cache-first — prevents ChunkLoadError after redeploys)
 * - Icons, manifest, favicon: Cache-first (immutable assets)
 * - API calls & HTML pages: Network-first → always fresh data
 * - Offline fallback: Show /offline.html when network unavailable
 *
 * Version bump forces SW update & cache refresh.
 */

const CACHE_NAME = "ao-copilot-v2";
const OFFLINE_URL = "/offline.html";

// Static assets to pre-cache on install
const PRECACHE_URLS = [
  "/offline.html",
  "/favicon.svg",
  "/favicon.ico",
  "/icons/icon-192.png",
  "/icons/icon-512.png",
  "/manifest.json",
];

// ── Install: pre-cache essential assets ──
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then((cache) => cache.addAll(PRECACHE_URLS))
      .then(() => self.skipWaiting())
  );
});

// ── Activate: clean up old caches ──
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((key) => key !== CACHE_NAME)
            .map((key) => caches.delete(key))
        )
      )
      .then(() => self.clients.claim())
  );
});

// ── Fetch handler ──
self.addEventListener("fetch", (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== "GET") return;

  // Skip cross-origin requests (analytics, fonts CDN, etc.)
  if (url.origin !== self.location.origin) return;

  // /_next/ chunks → NETWORK-FIRST (prevents ChunkLoadError after redeploy)
  // After a redeploy, chunk hashes change. Cache-first would serve stale
  // manifests that reference non-existent chunks → white screen of death.
  if (url.pathname.startsWith("/_next/")) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          if (response.ok) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
          }
          return response;
        })
        .catch(() => {
          return caches.match(request).then((cached) => {
            if (cached) return cached;
            return new Response("", { status: 504 });
          });
        })
    );
    return;
  }

  // Immutable static assets (icons, manifest) → cache-first
  if (
    url.pathname.startsWith("/icons/") ||
    url.pathname === "/manifest.json" ||
    url.pathname === "/favicon.svg" ||
    url.pathname === "/favicon.ico"
  ) {
    event.respondWith(
      caches.match(request).then((cached) => {
        if (cached) return cached;
        return fetch(request).then((response) => {
          if (response.ok) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
          }
          return response;
        });
      })
    );
    return;
  }

  // Pages & API → network-first with offline fallback
  event.respondWith(
    fetch(request)
      .then((response) => {
        // Optionally cache HTML pages for next offline visit
        if (response.ok && request.headers.get("accept")?.includes("text/html")) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
        }
        return response;
      })
      .catch(() => {
        // Network failed — try cache, then offline page
        return caches.match(request).then((cached) => {
          if (cached) return cached;
          // For navigation requests, show offline page
          if (request.mode === "navigate") {
            return caches.match(OFFLINE_URL);
          }
          // For other requests (API), return a minimal error response
          return new Response(
            JSON.stringify({ error: "offline", message: "Pas de connexion réseau" }),
            { status: 503, headers: { "Content-Type": "application/json" } }
          );
        });
      })
  );
});
