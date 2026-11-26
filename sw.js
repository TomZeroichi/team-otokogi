const CACHE='team-otokogi-v36';
const ASSETS=['./','./static/style.css','./static/app.js','./static/kyoki-logo-hi-192.png','./static/kyoki-logo-hi-512.png','./pages/shared-api.js','./pages/brand-concept.js','./pages/pwa.js','./pages/manifest.webmanifest'];
self.addEventListener('install',event=>{self.skipWaiting();event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(ASSETS)));});
self.addEventListener('activate',event=>event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(key=>key!==CACHE).map(key=>caches.delete(key)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',event=>{
  if(event.request.method!=='GET') return;
  const url=new URL(event.request.url);
  if(url.origin!==location.origin) return;
  const latest=event.request.mode==='navigate'||/\.(?:html|js|css|webmanifest)$/.test(url.pathname);
  event.respondWith(fetch(event.request,{cache:latest?'no-store':'default'}).then(response=>{
    if(response.ok){const copy=response.clone();caches.open(CACHE).then(cache=>cache.put(event.request,copy));}
    return response;
  }).catch(()=>caches.match(event.request,{ignoreSearch:true}).then(hit=>hit||caches.match('./'))));
});
