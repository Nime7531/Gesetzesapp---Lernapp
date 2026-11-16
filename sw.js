const CACHE='rubrum-pwa-v1';
const APP='./Rubrum%20mit%20Vollexport.html';
const CORE=['./','./index.html','./manifest.webmanifest','./icons/rubrum.svg',APP];
self.addEventListener('install',event=>{
  event.waitUntil((async()=>{
    const cache=await caches.open(CACHE);
    await cache.addAll(CORE);
    await self.skipWaiting();
  })());
});
self.addEventListener('activate',event=>{
  event.waitUntil((async()=>{
    const keys=await caches.keys();
    await Promise.all(keys.filter(k=>k.startsWith('rubrum-pwa-')&&k!==CACHE).map(k=>caches.delete(k)));
    await self.clients.claim();
  })());
});
self.addEventListener('fetch',event=>{
  const request=event.request;
  if(request.method!=='GET'||new URL(request.url).origin!==self.location.origin)return;
  if(request.mode==='navigate'){
    event.respondWith((async()=>{
      const cached=await caches.match(request,{ignoreSearch:true});
      if(cached)return cached;
      try{
        const response=await fetch(request);
        if(response.ok)(await caches.open(CACHE)).put(request,response.clone());
        return response;
      }catch(_){
        return (await caches.match(APP))||(await caches.match('./index.html'));
      }
    })());
    return;
  }
  const url=new URL(request.url);
  if(url.pathname.endsWith('.html')||url.pathname.endsWith('.webmanifest')||url.pathname.endsWith('.svg')){
    event.respondWith((async()=>{
      const cached=await caches.match(request);
      if(cached)return cached;
      const response=await fetch(request);
      if(response.ok)(await caches.open(CACHE)).put(request,response.clone());
      return response;
    })());
  }
});