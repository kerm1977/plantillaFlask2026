// service-worker.js

// Versión de la caché. Cámbiala para forzar la actualización del Service Worker y la caché.
const CACHE_NAME = 'la-tribu-pwa-cache-v1.0.7';

// Archivos esenciales para cachear durante la instalación.
const urlsToCache = [
    '/',
    '/offline.html', // Página para mostrar cuando no hay conexión
    '/static/manifest.json', // El manifest de la PWA
    '/static/css/main.css',
    '/static/css/bootstrap.css',
    '/static/css/bootstrap-icons.css',
    '/static/js/bootstrap.bundle.min.js',
    // Asegúrate de que las rutas a tus imágenes y otros assets sean correctas.
    '/static/uploads/icons/icon-192x192.jpg',
    '/static/uploads/icons/icon-512x512.jpg'
];

// Evento 'install': Se dispara cuando el Service Worker se instala.
self.addEventListener('install', (event) => {
    console.log('[Service Worker] Instalando...');
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('[Service Worker] Cacheando archivos esenciales');
                return cache.addAll(urlsToCache);
            })
            .catch((error) => {
                console.error('[Service Worker] Falló la caché de archivos esenciales:', error);
            })
    );
    // Forzar al nuevo Service Worker a activarse inmediatamente.
    self.skipWaiting();
});

// Evento 'activate': Se dispara cuando el Service Worker se activa.
self.addEventListener('activate', (event) => {
    console.log('[Service Worker] Activando...');
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    // Elimina las cachés antiguas que no coincidan con la versión actual.
                    if (cacheName !== CACHE_NAME) {
                        console.log('[Service Worker] Eliminando caché antigua:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
    // Toma el control de las páginas abiertas para que el Service Worker funcione de inmediato.
    return self.clients.claim();
});

// Evento 'fetch': Intercepta todas las solicitudes de red.
self.addEventListener('fetch', (event) => {
    // Solo procesa solicitudes GET.
    if (event.request.method !== 'GET') {
        return;
    }

    const url = new URL(event.request.url);
    const isStatic = url.pathname.startsWith('/static/');
    const isNavigation = event.request.mode === 'navigate' || event.request.headers.get('accept')?.includes('text/html');

    // Estrategia para páginas dinámicas: Network First, sin caché de HTML.
    if (isNavigation) {
        event.respondWith(
            fetch(event.request)
                .then((networkResponse) => networkResponse)
                .catch(() => caches.match('/offline.html'))
        );
        return;
    }

    // Estrategia para estáticos: Cache First con actualización desde red.
    if (isStatic) {
        event.respondWith(
            caches.match(event.request)
                .then((cachedResponse) => {
                    const fetchPromise = fetch(event.request)
                        .then((networkResponse) => {
                            if (networkResponse && networkResponse.status === 200) {
                                const responseToCache = networkResponse.clone();
                                caches.open(CACHE_NAME).then((cache) => {
                                    cache.put(event.request, responseToCache);
                                });
                            }
                            return networkResponse;
                        })
                        .catch(() => cachedResponse);
                    return cachedResponse || fetchPromise;
                })
        );
        return;
    }

    // Resto de solicitudes: red, con fallback a caché si existe.
    event.respondWith(
        fetch(event.request)
            .catch(() => caches.match(event.request))
    );
});