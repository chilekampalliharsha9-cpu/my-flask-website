const CACHE_NAME = 'disaster-prototype-v1';
const FILES_TO_CACHE = [
  '/',
  '/index.html',
  '/styles.css',
  '/app.js',
  '/precautions.json',
  '/README.md'
];

self.addEventListener('install', (evt) => {
  evt.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(FILES_TO_CACHE))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (evt) => {
  evt.waitUntil(
    caches.keys().then(keys => Promise.all(
      keys.map(k => { if(k !== CACHE_NAME) return caches.delete(k); })
    ))
  );
  self.clients.claim();
});

// Network-first for API calls, cache-first for navigation/static assets
self.addEventListener('fetch', (evt) => {
  const url = new URL(evt.request.url);
  // treat API endpoints specially
  if(url.hostname.includes('open-meteo.com') || url.hostname.includes('overpass-api.de') || url.hostname.includes('router.project-osrm.org') || url.hostname.includes('nominatim.openstreetmap.org')){
    evt.respondWith(
      fetch(evt.request).then(res => {
        const copy = res.clone();
        caches.open(CACHE_NAME).then(cache => cache.put(evt.request, copy));
        return res;
      }).catch(()=>caches.match(evt.request))
    );
    return;
  }

  // for local files, cache-first
  evt.respondWith(caches.match(evt.request).then(resp=>resp||fetch(evt.request)));
});
