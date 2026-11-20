const scope = new URL(self.registration.scope);
const cachePrefix = 'rubrum-offline:' + scope.pathname + ':';
const cacheName = cachePrefix + '7';
const home = new URL('./', scope).href;
const manifest = new URL('manifest.webmanifest', scope).href;
const syncPath = new URL('api/rubrum-snapshot', scope).href;

self.addEventListener('install', event => {
  event.waitUntil((async () => {
    const cache = await caches.open(cacheName);
    await cache.addAll([home, manifest].map(url => new Request(url, { cache: 'reload' })));
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter(key => key.startsWith(cachePrefix) && key !== cacheName)
      .map(key => caches.delete(key)));
    await self.clients.claim();
  })());
});

async function loadApp(request) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(home);
  try {
    const response = await fetch(request, { signal: AbortSignal.timeout(5000) });
    if (response.ok && !response.redirected && response.headers.get('content-type')?.includes('text/html')) {
      try { await cache.put(home, response.clone()); } catch { /* The existing offline copy may still be available. */ }
      return response;
    }
    return cached ?? response;
  } catch {
    return cached ?? Response.error();
  }
}

async function sync(request) {
  const unavailable = status => new Response(null, { status, headers: { 'Cache-Control': 'no-store' } });
  try {
    const config = await fetch(new URL('sync-server.json', scope), {
      cache: 'no-store', redirect: 'error', signal: AbortSignal.timeout(8000)
    });
    if (config.status === 404) return unavailable(404);
    if (!config.ok) return unavailable(503);
    const { endpoint } = await config.json();
    if (!endpoint) return unavailable(404);
    const target = new URL(endpoint);
    if (target.protocol !== 'https:' || target.origin === scope.origin ||
        target.username || target.password || target.search || target.hash ||
        target.pathname !== '/api/rubrum-snapshot') return unavailable(503);
    const headers = new Headers();
    for (const name of ['Authorization', 'Content-Type', 'If-Match', 'If-None-Match']) {
      const value = request.headers.get(name);
      if (value !== null) headers.set(name, value);
    }
    const response = await fetch(target, {
      method: request.method, headers, body: request.method === 'PUT' ? await request.blob() : undefined,
      cache: 'no-store', credentials: 'omit', redirect: 'error', signal: AbortSignal.timeout(175000)
    });
    const forwarded = new Headers({ 'Cache-Control': 'no-store' });
    for (const name of ['Content-Type', 'ETag', 'X-Rubrum-Sync']) {
      const value = response.headers.get(name);
      if (value !== null) forwarded.set(name, value);
    }
    return new Response(response.body, { status: response.status, headers: forwarded });
  } catch {
    return unavailable(503);
  }
}

self.addEventListener('fetch', event => {
  const request = event.request;
  if (request.url === syncPath && ['HEAD', 'GET', 'PUT'].includes(request.method)) {
    event.respondWith(sync(request));
    return;
  }
  const url = new URL(request.url);
  if (request.method !== 'GET' || url.origin !== scope.origin) return;
  if (request.mode === 'navigate' &&
      (url.pathname === scope.pathname || url.pathname === new URL('index.html', scope).pathname)) {
    event.respondWith(loadApp(request));
  } else if (request.url === manifest) {
    event.respondWith(caches.open(cacheName).then(async cache => (await cache.match(manifest)) ?? fetch(request)));
  }
});
