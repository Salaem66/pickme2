const CACHE_NAME = 'pickme-v1';
const urlsToCache = [
  '/',
  '/tech.html',
  '/manifest.json',
  '/pickme_logo.png',
  '/api/search'
];

// Installation du Service Worker
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Cache ouvert');
        return cache.addAll(urlsToCache);
      })
  );
});

// Activation du Service Worker
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            console.log('Suppression ancien cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// Interception des requêtes
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Retourner la ressource du cache si disponible
        if (response) {
          return response;
        }

        // Sinon, faire la requête réseau
        return fetch(event.request).then(response => {
          // Vérifier si la réponse est valide
          if (!response || response.status !== 200 || response.type !== 'basic') {
            return response;
          }

          // Cloner la réponse car elle ne peut être consommée qu'une fois
          const responseToCache = response.clone();

          caches.open(CACHE_NAME)
            .then(cache => {
              cache.put(event.request, responseToCache);
            });

          return response;
        }).catch(() => {
          // En cas d'erreur réseau, retourner une page d'erreur basique
          if (event.request.destination === 'document') {
            return new Response(
              '<!DOCTYPE html><html><head><title>PickMe - Hors ligne</title><meta name="viewport" content="width=device-width, initial-scale=1"></head><body style="font-family: Arial, sans-serif; text-align: center; padding: 50px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; min-height: 100vh; display: flex; align-items: center; justify-content: center; margin: 0;"><div><h1>🎬 PickMe</h1><p>Vous êtes hors ligne</p><p>Vérifiez votre connexion internet et réessayez</p></div></body></html>',
              { headers: { 'Content-Type': 'text/html' } }
            );
          }
        });
      })
  );
});

// Gestion des messages du client
self.addEventListener('message', event => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

// Gestion des clics sur les notifications
self.addEventListener('notificationclick', event => {
  console.log('Clic sur notification:', event);

  event.notification.close();

  // Ouvrir ou focuser la fenêtre PickMe
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(clientList => {
      // Si une fenêtre PickMe est déjà ouverte, la focuser
      for (const client of clientList) {
        if (client.url.includes('pickme.tv') && 'focus' in client) {
          return client.focus();
        }
      }

      // Sinon, ouvrir une nouvelle fenêtre
      if (clients.openWindow) {
        return clients.openWindow(event.notification.data?.url || 'https://app.pickme.tv');
      }
    })
  );
});