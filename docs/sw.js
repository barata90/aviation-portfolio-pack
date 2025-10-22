const SW_VERSION = 'v2';
function siteRoot(){ const parts = self.location.pathname.split('/').filter(Boolean); return parts.length ? '/' + parts[0] + '/' : '/'; }
const CORE = [
siteRoot(),
siteRoot() + 'index.html',
siteRoot() + 'assets/datasets.json'
];
self.addEventListener('install', (e) => {
e.waitUntil(caches.open('core-' + SW_VERSION).then(c => c.addAll(CORE)).then(()=> self.skipWaiting()));
});
self.addEventListener('activate', (e) => {
e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => !k.endsWith(SW_VERSION)).map(k => caches.delete(k)))));
self.clients.claim();
});
// Stale-while-revalidate for assets/.json and publish/.csv
self.addEventListener('fetch', (e) => {
const url = new URL(e.request.url);
const root = siteRoot();
const isSameOrigin = url.origin === location.origin;
const isCacheable = isSameOrigin && (url.pathname.startsWith(root + 'assets/') || url.pathname.startsWith(root + 'publish/'));
if (!isCacheable) return; // let browser handle others
e.respondWith((async () => {
const cache = await caches.open('data-' + SW_VERSION);
const cached = await cache.match(e.request);
const fetchPromise = fetch(e.request).then((network) => {
if (network && network.ok) cache.put(e.request, network.clone());
return network;
}).catch(() => cached);
return cached || fetchPromise;
})());
});
