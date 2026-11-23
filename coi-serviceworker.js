/* AudioLab Studio: cross-origin isolation service worker.
   GitHub Pages cannot send custom headers, so this worker adds them to every response.
   That makes the page "cross-origin isolated", which unlocks SharedArrayBuffer (the shared-memory engine),
   and it allows choosing the audio output device (iFi Gryphon etc.). */
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));
self.addEventListener('fetch', e => {
  const r = e.request;
  if (r.cache === 'only-if-cached' && r.mode !== 'same-origin') return;
  e.respondWith((async () => {
    let res;
    try { res = await fetch(r.mode === 'no-cors' ? new Request(r, { credentials: 'omit' }) : r); }
    catch (err) { return Response.error(); }
    if (res.status === 0) return res;
    const h = new Headers(res.headers);
    h.set('Cross-Origin-Opener-Policy', 'same-origin');
    h.set('Cross-Origin-Embedder-Policy', 'credentialless');
    h.set('Cross-Origin-Resource-Policy', 'cross-origin');
    if (r.mode === 'navigate') h.set('Permissions-Policy', 'speaker-selection=(self), microphone=(self), midi=(self)');
    return new Response(res.body, { status: res.status, statusText: res.statusText, headers: h });
  })());
});
