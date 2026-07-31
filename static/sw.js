// static/sw.js  —  La Tribu PWA Offline v8.0
// Estrategia: Cache-first (estáticos) + Stale-While-Revalidate (páginas) + Network-first (API)

const CACHE_NAME     = 'la-tribu-v10.7';
const STATIC_CACHE   = 'la-tribu-static-v10.7';
const PAGES_CACHE    = 'la-tribu-pages-v10.7';
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
    // Ignorar peticiones a dominios externos (Cloudflare, CDNs, etc.)
    if (url.origin !== self.location.origin) return;

    // 1. Uploads de usuarios → siempre Network, nunca cachear
    if (url.pathname.startsWith('/static/uploads/')) {
        event.respondWith(
            fetch(event.request).catch(() => new Response('', { status: 404 }))
        );
        return;
    }

    // 2. ESTÁTICOS (/static/) → Cache-first, actualiza en background
    if (url.pathname.startsWith('/static/')) {
        event.respondWith(
            caches.open(STATIC_CACHE).then(async cache => {
                const cached = await cache.match(event.request);
                const fetchPromise = fetch(event.request).then(res => {
                    if (res && res.status === 200) cache.put(event.request, res.clone());
                    return res;
                }).catch(() => null);
                return cached || await fetchPromise || new Response('', { status: 404 });
            })
        );
        return;
    }

    // 2. Páginas dinámicas admin → siempre Network-first (sin caché)
    const NETWORK_ONLY = ['/gestor-fechas', '/dashboard', '/eventos', '/detalles_evento'];
    if (NETWORK_ONLY.some(p => url.pathname.startsWith(p))) {
        event.respondWith(
            fetch(event.request).catch(() => caches.match(event.request))
        );
        return;
    }

    // 3. API (/api/) → Network-first, SIN caché para evitar datos obsoletos
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(
            fetch(event.request).catch(() => {
                return new Response(JSON.stringify([]), {
                    status: 200,
                    headers: { 'Content-Type': 'application/json' }
                });
            })
        );
        return;
    }

    // 3. NAVEGACIÓN (HTML) → Network-first, caché solo si no hay red
    event.respondWith(
        caches.open(PAGES_CACHE).then(async cache => {
            try {
                const fresh = await fetch(event.request);
                if (fresh && fresh.status === 200) {
                    cache.put(event.request, fresh.clone());
                }
                return fresh;
            } catch (err) {
                // Sin red → intentar caché
                const cached = await cache.match(event.request);
                if (cached) return cached;
                // Sin caché y sin red → página offline
                if (event.request.mode === 'navigate') {
                    return cache.match(OFFLINE_URL) || caches.match(OFFLINE_URL);
                }
                return new Response('Sin conexión', { status: 503 });
            }
        })
    );
});
