const CACHE_NAME = 'jarvis-companion-shell-v1';
const SHELL_ASSETS = [
    '/static/manifest.json',
    '/static/icon.svg',
    '/static/offline.html',
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => cache.addAll(SHELL_ASSETS))
            .then(() => self.skipWaiting())
    );
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys()
            .then((keys) => Promise.all(
                keys
                    .filter((key) => key.startsWith('jarvis-companion-shell-') && key !== CACHE_NAME)
                    .map((key) => caches.delete(key))
            ))
            .then(() => self.clients.claim())
    );
});

self.addEventListener('fetch', (event) => {
    const request = event.request;
    if (request.method !== 'GET' || new URL(request.url).origin !== self.location.origin) return;

    if (request.mode === 'navigate') {
        event.respondWith(
            fetch(request).catch(async () => {
                const offlinePage = await caches.match('/static/offline.html');
                return offlinePage || Response.error();
            })
        );
        return;
    }

    if (new URL(request.url).pathname.startsWith('/static/')) {
        event.respondWith(
            caches.open(CACHE_NAME).then(async (cache) => {
                const cached = await cache.match(request);
                if (cached) return cached;

                const response = await fetch(request);
                if (response.ok && response.type === 'basic') {
                    await cache.put(request, response.clone());
                }
                return response;
            })
        );
    }
});