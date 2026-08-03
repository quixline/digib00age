// digib00age — sw.js
// Minimal service worker: app-shell cache-first for static assets,
// network-first for page navigations and API calls. Served at /sw.js via a
// dedicated FastAPI route so it controls the full / scope.

// The placeholder token below is substituted server-side (backend/main.py's
// /sw.js route) with a hash of every file under frontend/ — changes
// automatically whenever any served file changes, so the browser's SW
// update check (which compares this file's bytes) notices and the activate
// handler below evicts the stale cache, instead of relying on someone
// remembering to bump a hardcoded version string by hand.
const CACHE_NAME = 'digib00age-shell-' + 'ASSET_VERSION_TOKEN';

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

// ── Fetch: network-first for navigations/API, cache-first for static assets ──

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Network-first for API calls — always want fresh data. Cache fallback only
  // makes sense for GET: nothing non-GET is ever cached (see caches.put calls
  // below), so falling back on a failed POST/PUT/DELETE/PATCH always misses,
  // resolving to undefined — which respondWith() turns into its own opaque
  // "Failed to convert value to 'Response'" error, masking whatever actually
  // went wrong on a mutating request (e.g. a long batch-process call) behind
  // a second, unrelated failure. Let those reject with the real fetch error
  // instead.
  if (url.pathname.startsWith('/api/')) {
    if (event.request.method !== 'GET') {
      event.respondWith(fetch(event.request));
      return;
    }
    event.respondWith(
      fetch(event.request).catch(() => caches.match(event.request))
    );
    return;
  }

  // Network-first for page navigations (BUG-032): a newly-installed SW
  // activates and claims clients asynchronously, so cache-first here could
  // still serve the *previous* HTML shell — e.g. missing a <link> tag added
  // in the same edit that triggered this update — on the very navigation
  // that should have picked it up. Falls back to cache only when offline.
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          if (response.ok) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
          }
          return response;
        })
        .catch(() => caches.match(event.request))
    );
    return;
  }

  // Cache-first for everything else (static assets)
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
