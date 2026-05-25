// static/sw.js
const CACHE_NAME = 'la-tribu-pwa-v5.0';

// Archivos esenciales que se cachean en la instalación para funcionar offline
const PRECACHE_URLS = [
    '/',
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

// INSTALL: precachear todos los estáticos esenciales
self.addEventListener('install', (event) => {
    self.skipWaiting();
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return Promise.allSettled(
                PRECACHE_URLS.map(url =>
                    cache.add(url).catch(err => console.warn('[SW] No se pudo cachear:', url, err))
                )
            );
        })
    );
});

// ACTIVATE: eliminar cachés viejas
self.addEventListener('activate', (event) => {
    event.waitUntil(
        Promise.all([
            self.clients.claim(),
            caches.keys().then(keys =>
                Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
            )
        ])
    );
});

// FETCH: Cache-first para estáticos, Network-first para páginas/API
self.addEventListener('fetch', (event) => {
    if (event.request.method !== 'GET') return;

    const url = new URL(event.request.url);

    // Ignorar peticiones de extensiones del navegador
    if (!url.protocol.startsWith('http')) return;

    // ESTRATEGIA: Cache-first para recursos estáticos
    if (url.pathname.startsWith('/static/')) {
        event.respondWith(
            caches.match(event.request).then(cached => {
                if (cached) return cached;
                return fetch(event.request).then(response => {
                    if (response && response.status === 200) {
                        caches.open(CACHE_NAME).then(cache => cache.put(event.request, response.clone()));
                    }
                    return response;
                }).catch(() => caches.match(event.request));
            })
        );
        return;
    }

    // ESTRATEGIA: Network-first para páginas HTML y API
    event.respondWith(
        fetch(event.request).then(response => {
            if (response && response.status === 200) {
                caches.open(CACHE_NAME).then(cache => cache.put(event.request, response.clone()));
            }
            return response;
        }).catch(() => {
            return caches.match(event.request).then(cached => {
                if (cached) return cached;
                // Fallback offline: devolver la página principal cacheada
                return caches.match('/');
            });
        })
    );
});