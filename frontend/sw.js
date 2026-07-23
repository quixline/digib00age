// ComicVault — sw.js
// Minimal service worker: app-shell cache-first for static assets,
// network-first for API calls. Served at /sw.js via a dedicated FastAPI
// route so it controls the full / scope.

const CACHE_NAME = 'comicvault-shell-v1';

const APP_SHELL = [
  '/',
  '/static/css/tokens-base.css',
  '/static/css/tokens-dark.css',
  '/static/css/tokens-light.css',
  '/static/css/style.css',
  '/static/js/app.js',
  '/static/js/auth.js',
  '/static/js/pwa.js',
  '/static/js/admin.js',
  '/static/js/filterDropdown.js',
  '/static/js/editor_full.js',
  '/static/js/processingTools.js',
  '/static/js/filePicker.js',
  '/static/manifest.json',
  '/static/images/favicon.png',
  '/static/images/lockup-light.png',
  '/static/images/lockup-dark.png',
  '/static/images/icons/icon-192.png',
  '/static/images/icons/icon-512.png',
];

// ── Install: pre-cache app shell ──────────────────────────────────────────────

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL))
  );
  self.skipWaiting();
});

// ── Activate: remove old caches ───────────────────────────────────────────────

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))
      )
    )
  );
  self.clients.claim();
});

// ── Fetch: cache-first for static, network-first for API ─────────────────────

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Network-first for API calls — always want fresh data
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(event.request).catch(() => caches.match(event.request))
    );
    return;
  }

  // Cache-first for everything else (static assets + HTML shells)
  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) return cached;
      return fetch(event.request).then((response) => {
        // Only cache successful same-origin responses
        if (
          response.ok &&
          url.origin === self.location.origin
        ) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
        }
        return response;
      });
    })
  );
});
