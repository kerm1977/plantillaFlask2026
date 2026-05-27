// static/sw.js  —  La Tribu PWA Offline v8.0
// Estrategia: Cache-first (estáticos) + Stale-While-Revalidate (páginas) + Network-first (API)

const CACHE_NAME     = 'la-tribu-v8.0';
const STATIC_CACHE   = 'la-tribu-static-v8.0';
const PAGES_CACHE    = 'la-tribu-pages-v8.0';
const OFFLINE_URL    = '/offline';

// ── Shell completo precacheado al instalar ─────────────────────────────────
const PRECACHE_SHELL = [
    '/',
    OFFLINE_URL,
    '/rifas',
    '/manifest.json',
    '/static/logo.png',
    '/static/css/bootstrap.css',
    '/static/css/bootstrap-icons.css',
    '/static/css/global.css',
    '/static/css/base.css',
    '/static/css/main.css',
    '/static/css/fonts/bootstrap-icons.woff2',
    '/static/js/bootstrap.bundle.min.js',
    '/static/js/validaciones.js',
    '/static/js/setup_global.js',
    '/static/js/auth_ui.js',
    '/static/js/home.js',
    '/static/js/calendario_motor.js',
    '/static/js/calendario_export.js'
];

// ── INSTALL: precachear shell inmediatamente ───────────────────────────────
self.addEventListener('install', event => {
    self.skipWaiting();
    event.waitUntil(
        Promise.all([
            caches.open(STATIC_CACHE).then(cache =>
                Promise.allSettled(
                    PRECACHE_SHELL
                        .filter(u => u.startsWith('/static/') || u === '/manifest.json' || u === '/static/logo.png')
                        .map(u => cache.add(u).catch(() => {}))
                )
            ),
            caches.open(PAGES_CACHE).then(cache =>
                Promise.allSettled(
                    PRECACHE_SHELL
                        .filter(u => !u.startsWith('/static/') && u !== '/manifest.json')
                        .map(u => cache.add(u).catch(() => {}))
                )
            )
        ])
    );
});

// ── ACTIVATE: limpiar cachés viejas y tomar control ───────────────────────
self.addEventListener('activate', event => {
    event.waitUntil(
        Promise.all([
            self.clients.claim(),
            caches.keys().then(keys =>
                Promise.all(
                    keys
                        .filter(k => k !== STATIC_CACHE && k !== PAGES_CACHE)
                        .map(k => caches.delete(k))
                )
            )
        ])
    );
});

// ── FETCH: estrategia por tipo de recurso ────────────────────────────────
self.addEventListener('fetch', event => {
    if (event.request.method !== 'GET') return;
    const url = new URL(event.request.url);
    if (!url.protocol.startsWith('http')) return;

    // 1. ESTÁTICOS (/static/) → Cache-first, actualiza en background
    if (url.pathname.startsWith('/static/')) {
        event.respondWith(
            caches.open(STATIC_CACHE).then(async cache => {
                const cached = await cache.match(event.request);
                const fetchPromise = fetch(event.request).then(res => {
                    if (res && res.status === 200) cache.put(event.request, res.clone());
                    return res;
                }).catch(() => null);
                return cached || await fetchPromise;
            })
        );
        return;
    }

    // 2. API (/api/) → Network-first, guarda en caché de páginas
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(
            fetch(event.request).then(res => {
                if (res && res.status === 200) {
                    caches.open(PAGES_CACHE).then(c => c.put(event.request, res.clone()));
                }
                return res;
            }).catch(() => caches.match(event.request))
        );
        return;
    }

    // 3. NAVEGACIÓN (HTML) → Stale-While-Revalidate
    //    Sirve caché instantáneamente Y actualiza en background.
    //    Si no hay caché Y no hay red → página offline.
    event.respondWith(
        caches.open(PAGES_CACHE).then(async cache => {
            const cached = await cache.match(event.request);

            const networkFetch = fetch(event.request).then(res => {
                if (res && res.status === 200) {
                    cache.put(event.request, res.clone());
                }
                return res;
            }).catch(() => null);

            if (cached) {
                // Sirve caché ahora, actualiza en background
                networkFetch; // dispara sin await
                return cached;
            }

            // No está en caché → esperar la red
            const fresh = await networkFetch;
            if (fresh) return fresh;

            // Sin red y sin caché → página offline
            if (event.request.mode === 'navigate') {
                return cache.match(OFFLINE_URL) || caches.match(OFFLINE_URL);
            }
            return new Response('Sin conexión', { status: 503 });
        })
    );
});