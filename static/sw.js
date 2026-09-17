// static/sw.js  —  La Tribu PWA Offline v8.0
// Estrategia: Cache-first (estáticos) + Stale-While-Revalidate (páginas) + Network-first (API)

const CACHE_NAME     = 'la-tribu-v10.16';
const STATIC_CACHE   = 'la-tribu-static-v10.16';
const PAGES_CACHE    = 'la-tribu-pages-v10.16';
const OFFLINE_DATA_CACHE = 'la-tribu-offline-data-v1';
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

async function notifyOfflineClients(message) {
    const clients = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
    clients.forEach(client => client.postMessage(message));
}

async function saveOfflineState(cache, state) {
    await cache.put('/api/offline/download-state', new Response(JSON.stringify(state), { headers: { 'Content-Type': 'application/json' } }));
}

async function getOfflineState() {
    const cache = await caches.open(OFFLINE_DATA_CACHE);
    const response = await cache.match('/api/offline/download-state');
    return response ? response.json() : null;
}

async function downloadOfflineContent() {
    const manifestResponse = await fetch('/api/offline/manifest', { credentials: 'include', cache: 'no-store' });
    if (!manifestResponse.ok) throw new Error(`Inventario offline: HTTP ${manifestResponse.status}`);
    const manifest = await manifestResponse.json();
    const fileMap = new Map(manifest.files.map(file => [file.url, file]));
    const entries = [...manifest.pages, ...manifest.files.map(file => file.url)];
    const cache = await caches.open(OFFLINE_DATA_CACHE);
    let completed = 0;
    let downloadedBytes = 0;
    let reused = 0;
    const failures = [];
    const state = { status: 'running', version: manifest.version, completed, total: entries.length, downloadedBytes, totalBytes: manifest.total_bytes, reused, failures, updatedAt: new Date().toISOString() };
    await saveOfflineState(cache, state);
    await notifyOfflineClients({ type: 'OFFLINE_DOWNLOAD_START', ...state });
    for (const url of entries) {
        const file = fileMap.get(url);
        const cached = file ? await cache.match(url) : null;
        if (file && cached && cached.headers.get('X-LaTribu-Offline-Version') === file.version) {
            completed += 1;
            reused += 1;
            downloadedBytes += file.size;
            await notifyOfflineClients({ type: 'OFFLINE_DOWNLOAD_LOG', level: 'info', message: `Ya descargado, se conserva: ${url}` });
        } else {
            await notifyOfflineClients({ type: 'OFFLINE_DOWNLOAD_LOG', level: 'info', message: `Descargando: ${url}` });
            try {
                const response = await fetch(url, { credentials: 'include', cache: 'no-store' });
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                if (file) {
                    const headers = new Headers(response.headers);
                    headers.set('X-LaTribu-Offline-Version', file.version);
                    await cache.put(url, new Response(response.body, { status: response.status, statusText: response.statusText, headers }));
                    downloadedBytes += file.size;
                } else {
                    await cache.put(url, response.clone());
                }
                await notifyOfflineClients({ type: 'OFFLINE_DOWNLOAD_LOG', level: 'success', message: `Guardado: ${url}` });
            } catch (error) {
                failures.push({ url, error: error.message, at: new Date().toISOString() });
                await notifyOfflineClients({ type: 'OFFLINE_DOWNLOAD_LOG', level: 'error', message: `Error ${error.message}: ${url}` });
            }
            completed += 1;
        }
        Object.assign(state, { completed, downloadedBytes, reused, failures: [...failures], updatedAt: new Date().toISOString() });
        await saveOfflineState(cache, state);
        await notifyOfflineClients({ type: 'OFFLINE_DOWNLOAD_PROGRESS', ...state });
    }
    Object.assign(state, { status: failures.length ? 'completed_with_errors' : 'completed', completedAt: new Date().toISOString() });
    await saveOfflineState(cache, state);
    await cache.put('/api/offline/manifest-snapshot', new Response(JSON.stringify({ ...manifest, downloadedAt: state.completedAt, failures }), { headers: { 'Content-Type': 'application/json' } }));
    await notifyOfflineClients({ type: 'OFFLINE_DOWNLOAD_COMPLETE', ...state });
}

self.addEventListener('message', event => {
    if (!event.data) return;
    if (event.data.type === 'SKIP_WAITING') self.skipWaiting();
    if (event.data.type === 'DOWNLOAD_ALL_OFFLINE') {
        event.waitUntil(downloadOfflineContent().catch(async error => {
            const cache = await caches.open(OFFLINE_DATA_CACHE);
            const previous = await getOfflineState() || {};
            const state = { ...previous, status: 'interrupted', error: error.message, updatedAt: new Date().toISOString() };
            await saveOfflineState(cache, state);
            await notifyOfflineClients({ type: 'OFFLINE_DOWNLOAD_ERROR', ...state });
        }));
    }
    if (event.data.type === 'GET_OFFLINE_DOWNLOAD_STATE') {
        event.waitUntil(getOfflineState().then(state => notifyOfflineClients({ type: 'OFFLINE_DOWNLOAD_STATE', state })));
    }
});

// ── ACTIVATE: limpiar cachés viejas y tomar control ───────────────────────
self.addEventListener('activate', event => {
    event.waitUntil(
        Promise.all([
            self.clients.claim(),
            caches.keys().then(keys =>
                Promise.all(
                    keys
                        .filter(k => k !== STATIC_CACHE && k !== PAGES_CACHE && k !== OFFLINE_DATA_CACHE)
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

    // 1. Uploads de usuarios → red normalmente, copia offline cuando no hay conexión
    if (url.pathname.startsWith('/static/uploads/')) {
        event.respondWith(
            fetch(event.request).catch(() => caches.open(OFFLINE_DATA_CACHE).then(cache => cache.match(event.request)))
        );
        return;
    }

    // 2. ESTÁTICOS (/static/) → Cache-first, actualiza en background
    if (url.pathname.startsWith('/static/')) {
        event.respondWith(
            caches.open(STATIC_CACHE).then(async cache => {
                const cached = await caches.match(event.request);
                const fetchPromise = fetch(event.request).then(res => {
                    if (res && res.status === 200) cache.put(event.request, res.clone());
                    return res;
                }).catch(() => null);
                return cached || await fetchPromise || new Response('', { status: 404 });
            })
        );
        return;
    }

    // 2. Páginas dinámicas admin y cotizador → siempre Network-first (sin caché)
    const NETWORK_ONLY = ['/gestor-fechas', '/dashboard', '/eventos', '/detalles_evento', '/cotizador', '/caminatas-2027'];
    if (NETWORK_ONLY.some(p => url.pathname.startsWith(p))) {
        event.respondWith(
            fetch(event.request, { cache: 'no-store' }).catch(() => caches.match(event.request))
        );
        return;
    }

    // 3. API (/api/) → Network-first, SIN caché para evitar datos obsoletos
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(
            fetch(event.request, { cache: 'no-store' }).catch(() => {
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
                const fresh = await fetch(event.request, { cache: 'no-store' });
                if (fresh && fresh.status === 200) {
                    cache.put(event.request, fresh.clone());
                }
                return fresh;
            } catch (err) {
                // Sin red → intentar caché
                const cached = await caches.match(event.request);
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
