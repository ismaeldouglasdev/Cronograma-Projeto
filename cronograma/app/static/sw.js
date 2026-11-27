const CACHE_NAME = 'ritmoexato-v2';
const OFFLINE_URL = '/static/offline.html';
const STATIC_ASSETS = [
  '/app',
  '/static/index.html',
  '/static/style.css',
  '/static/app.js',
  '/static/auth.js',
  '/static/store.js',
  '/static/foco.js',
  '/static/theme.js',
  '/static/theme-init.js',
  '/static/i18n.js',
  '/static/svg.js',
  '/static/logger.js',
  '/static/boot.js',
  '/static/landing.html',
  '/static/landing-tilt.js',
  '/static/manifest.json',
  OFFLINE_URL,
  'https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Outfit:wght@400;500;600;700;800;900&display=swap',
  'https://cdn.jsdelivr.net/npm/chart.js'
];

const CACHE_STRATEGIES = {
  STATIC: 'cache-first',
  API: 'network-first',
  FONTS: 'stale-while-revalidate'
};

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => Promise.allSettled(
        STATIC_ASSETS.map((url) => cache.add(new Request(url, { credentials: 'same-origin' })))
      ))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME)
          .map((name) => caches.delete(name))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  if (request.method !== 'GET') {
    return;
  }

  if (isAuthRequest(url)) {
    event.respondWith(networkOnlyStrategy(request));
    return;
  }

  if (url.pathname.startsWith('/auth/') || url.pathname.startsWith('/api/')) {
    event.respondWith(networkFirstStrategy(request));
    return;
  }

  if (url.pathname.startsWith('/static/') || url.pathname.startsWith('/icon_images/')) {
    event.respondWith(cacheFirstStrategy(request));
    return;
  }

  if (url.hostname === 'fonts.googleapis.com' || url.hostname === 'fonts.gstatic.com' || url.hostname === 'cdn.jsdelivr.net') {
    event.respondWith(staleWhileRevalidate(request));
    return;
  }

  event.respondWith(networkFirstStrategy(request));
});

function isAuthRequest(url) {
  return url.pathname === '/auth' ||
    url.pathname.startsWith('/auth/') ||
    url.pathname.includes('/auth/');
}

async function networkOnlyStrategy(request) {
  try {
    return await fetch(request);
  } catch (error) {
    return new Response('Offline', { status: 503, statusText: 'Service Unavailable' });
  }
}

async function cacheFirstStrategy(request) {
  const cached = await caches.match(request);
  if (cached) {
    return cached;
  }
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    return new Response('Offline', { status: 503, statusText: 'Service Unavailable' });
  }
}

async function networkFirstStrategy(request) {
  try {
    const response = await fetch(request);
    if (response.ok && !isAuthRequest(new URL(request.url))) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    const cached = await caches.match(request);
    if (cached) {
      return cached;
    }
    if (request.mode === 'navigate') {
      const offlinePage = await caches.match(OFFLINE_URL);
      if (offlinePage) return offlinePage;
    }
    return new Response('Offline', { status: 503, statusText: 'Service Unavailable' });
  }
}

async function staleWhileRevalidate(request) {
  const cached = await caches.match(request);
  const fetchPromise = fetch(request)
    .then((response) => {
      if (response.ok) {
        const cache = caches.open(CACHE_NAME);
        cache.then(c => c.put(request, response.clone()));
      }
      return response;
    })
    .catch(() => cached);
  return cached || fetchPromise;
}

self.addEventListener('message', (event) => {
  if (event.data === 'skipWaiting') {
    self.skipWaiting();
  }
  if (event.data === 'getVersion' && event.ports[0]) {
    event.ports[0].postMessage({ version: CACHE_NAME });
  }
});
