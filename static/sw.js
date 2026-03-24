// static/sw.js
// Versión de la caché.
const CACHE_NAME = 'la-tribu-pwa-cache-v4.0';

// Archivos esenciales mínimos para arrancar el modo Offline y validar la PWA
const urlsToCache = [
    '/',
    '/manifest.json'
];

// Evento 'install': Se dispara cuando el Service Worker se instala.
self.addEventListener('install', (event) => {
    console.log('[Service Worker] Instalando y forzando activación...');
    // Forzar al nuevo Service Worker a activarse inmediatamente.
    self.skipWaiting();
    
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('[Service Worker] Cacheando archivos esenciales');
                // Usamos allSettled para que no falle si falta algún archivo
                return Promise.allSettled(
                    urlsToCache.map(url => cache.add(url).catch(err => console.warn(`Fallo al cachear: ${url}`, err)))
                );
            })
    );
});

// Evento 'activate': Se limpia la basura vieja y toma el control
self.addEventListener('activate', (event) => {
    console.log('[Service Worker] Activando...');
    // Toma el control de las páginas abiertas para que funcione de inmediato.
    event.waitUntil(self.clients.claim());

    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('[Service Worker] Eliminando caché antigua:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});

// Evento 'fetch': Intercepta todas las solicitudes de red.
self.addEventListener('fetch', (event) => {
    // Solo procesar solicitudes GET.
    if (event.request.method !== 'GET') return;

    const requestUrl = new URL(event.request.url);

    // ESTRATEGIA 1: CACHE FIRST (Caché primero, luego red)
    // Usamos esto para recursos estáticos (Imágenes, CSS, JS, Íconos).
    // Esto es lo que Chrome exige para validar rápidamente la PWA.
    if (requestUrl.pathname.startsWith('/static/')) {
        event.respondWith(
            caches.match(event.request).then((cachedResponse) => {
                if (cachedResponse) {
                    return cachedResponse;
                }
                return fetch(event.request).then((networkResponse) => {
                    if (networkResponse && networkResponse.status === 200) {
                        const responseToCache = networkResponse.clone();
                        caches.open(CACHE_NAME).then((cache) => {
                            cache.put(event.request, responseToCache);
                        });
                    }
                    return networkResponse;
                }).catch(() => {
                    console.warn('[SW] Recurso estático no disponible offline');
                });
            })
        );
    } 
    // ESTRATEGIA 2: NETWORK FIRST (Red primero, respaldo de Caché)
    // Usamos esto para la página principal y la API. 
    // Asegura que los usuarios SIEMPRE vean los eventos nuevos si tienen internet.
    else {
        event.respondWith(
            fetch(event.request).then((networkResponse) => {
                // Guardamos en caché la respuesta fresca
                if (networkResponse && networkResponse.status === 200) {
                    const responseToCache = networkResponse.clone();
                    caches.open(CACHE_NAME).then((cache) => {
                        cache.put(event.request, responseToCache);
                    });
                }
                return networkResponse;
            }).catch(() => {
                // Si falla la red (Modo Offline real), buscamos en caché
                console.log('[SW] Sin conexión, sirviendo desde caché:', event.request.url);
                return caches.match(event.request);
            })
        );
    }
});