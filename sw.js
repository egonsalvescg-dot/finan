/*
 * Service Worker — Finanças
 *
 * Estratégia:
 *   - index.html / "/" : NETWORK-FIRST com fallback ao cache.
 *     (evita o problema clássico de PWA cacheada que nunca atualiza)
 *   - manifest.json e ícones: STALE-WHILE-REVALIDATE.
 *   - Outros assets GET: cache-first com revalidação em background.
 */
const VERSION = 'financas-v3';
const CORE_ASSETS = [
  './',
  './index.html',
  './manifest.json',
  './icon.svg'
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(VERSION).then(c =>
      // addAll é all-or-nothing; usamos map + put p/ tolerar falhas pontuais
      Promise.all(CORE_ASSETS.map(url =>
        fetch(url, { cache: 'no-cache' })
          .then(res => res.ok ? c.put(url, res) : null)
          .catch(() => null)
      ))
    ).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== VERSION).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

const isHTMLRequest = (req) => {
  if (req.mode === 'navigate') return true;
  const accept = req.headers.get('accept') || '';
  return accept.includes('text/html');
};

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  // Só interceptamos mesma origem
  if (url.origin !== self.location.origin) return;

  if (isHTMLRequest(req)) {
    // network-first
    e.respondWith(
      fetch(req).then(res => {
        if (res && res.ok) {
          const clone = res.clone();
          caches.open(VERSION).then(c => c.put('./index.html', clone));
        }
        return res;
      }).catch(() => caches.match('./index.html').then(r => r || caches.match('./')))
    );
    return;
  }

  // Outros: stale-while-revalidate
  e.respondWith(
    caches.match(req).then(cached => {
      const network = fetch(req).then(res => {
        if (res && res.ok && res.type === 'basic') {
          const clone = res.clone();
          caches.open(VERSION).then(c => c.put(req, clone));
        }
        return res;
      }).catch(() => cached);
      return cached || network;
    })
  );
});

self.addEventListener('message', (e) => {
  if (e.data === 'skipWaiting') self.skipWaiting();
});
