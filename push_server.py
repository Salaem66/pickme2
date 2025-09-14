#!/usr/bin/env python3
"""
Serveur de notifications push pour PickMe
Envoie des vraies notifications push sur écran verrouillé
"""

import json
import os
import time
from pywebpush import webpush, WebPushException
from supabase import create_client, Client
import asyncio
from typing import List, Dict, Any

class PushNotificationServer:
    def __init__(self):
        # Configuration Supabase
        self.supabase_url = "https://utzflwmghpojlsthyuqf.supabase.co"
        self.supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV0emZsd21naHBvamxzdGh5dXFmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc1NDQxOTAsImV4cCI6MjA3MzEyMDE5MH0.j5qMspjG6FTN69DPwI0otqjw7Yp5lbbFadflpkjNvYc"
        self.supabase = create_client(self.supabase_url, self.supabase_key)

        # Clés VAPID pour les notifications push (générées automatiquement)
        self.vapid_private_key = """-----BEGIN PRIVATE KEY-----
MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQg0gQELt1N4oZGH2YC
rQP9LRm1O6iYxNxrUNZEw8x7LaqhRANCAASeKXpHAw5N2XPgdCBKtaYJJKyPsY7X
6xNVfOd8p6dGFpXGkYtJ0TzQ2iAKpF1LzPL4Y5BqNzrW8HzRk2V9nQRm
-----END PRIVATE KEY-----"""

        self.vapid_public_key = "BJ4pekcDDk3Zc-B0IEq1pgkkrI-xjtfrE1V853ynp0YWlcaRi0nRPNDaIAqkXUvM8vhjkGo3OtbwfNGTZX2dBGY"
        self.vapid_email = "mael.sivenboren@gmail.com"

    async def get_all_subscriptions(self) -> List[Dict]:
        """Récupère tous les abonnements push actifs"""
        try:
            response = self.supabase.table('push_subscriptions').select('*').eq('is_active', True).execute()
            return response.data
        except Exception as e:
            print(f"Erreur récupération subscriptions: {e}")
            return []

    def send_push_to_subscription(self, subscription_data: Dict, notification: Dict):
        """Envoie une notification push à un abonnement"""
        try:
            subscription_info = {
                "endpoint": subscription_data['endpoint'],
                "keys": {
                    "p256dh": subscription_data['p256dh'],
                    "auth": subscription_data['auth']
                }
            }

            payload = {
                "title": f"📢 PickMe - {notification['type'].title()}",
                "body": notification['message'],
                "icon": "/pickme_logo.png",
                "badge": "/pickme_logo.png",
                "tag": f"admin-{notification['id']}",
                "requireInteraction": True,
                "data": {
                    "url": "/",
                    "notificationId": notification['id']
                }
            }

            webpush(
                subscription_info=subscription_info,
                data=json.dumps(payload),
                vapid_private_key=self.vapid_private_key,
                vapid_claims={
                    "sub": f"mailto:{self.vapid_email}",
                }
            )

            print(f"✅ Push envoyée à {subscription_data['user_id']}")
            return True

        except WebPushException as e:
            print(f"❌ Erreur WebPush: {e}")
            # Désactiver les abonnements expirés
            if e.response and e.response.status_code in [410, 404]:
                self.deactivate_subscription(subscription_data['id'])
            return False

        except Exception as e:
            print(f"❌ Erreur envoi push: {e}")
            return False

    def deactivate_subscription(self, subscription_id: str):
        """Désactive un abonnement expiré"""
        try:
            self.supabase.table('push_subscriptions').update({
                'is_active': False
            }).eq('id', subscription_id).execute()
            print(f"🗑️ Abonnement {subscription_id} désactivé")
        except Exception as e:
            print(f"Erreur désactivation subscription: {e}")

    async def broadcast_notification(self, notification: Dict):
        """Diffuse une notification à tous les abonnements actifs"""
        print(f"📢 Broadcasting notification: {notification['message']}")

        subscriptions = await self.get_all_subscriptions()
        print(f"📱 {len(subscriptions)} abonnements trouvés")

        if not subscriptions:
            print("⚠️ Aucun abonnement push trouvé")
            return

        success_count = 0
        for subscription in subscriptions:
            if self.send_push_to_subscription(subscription, notification):
                success_count += 1

                # Enregistrer la livraison
                try:
                    self.supabase.table('notification_deliveries').insert({
                        'notification_id': notification['id'],
                        'user_id': subscription['user_id']
                    }).execute()
                except Exception as e:
                    print(f"Erreur enregistrement livraison: {e}")

        print(f"✅ {success_count}/{len(subscriptions)} notifications envoyées")

    def listen_for_notifications(self):
        """Écoute les nouvelles notifications via Supabase Realtime"""
        print("🔔 Serveur push démarré - En attente des notifications...")

        def handle_notification(payload):
            notification = payload.get('payload')
            if notification:
                # Exécuter la diffusion en arrière-plan
                asyncio.create_task(self.broadcast_notification(notification))

        # S'abonner aux notifications admin via Realtime
        channel = self.supabase.channel('admin_notifications')
        channel.on('broadcast', handle_notification).subscribe()

        print("✅ Connecté au canal Supabase Realtime")

        # Garder le serveur actif
        try:
            asyncio.get_event_loop().run_forever()
        except KeyboardInterrupt:
            print("\n🛑 Serveur push arrêté")

if __name__ == "__main__":
    print("🚀 Démarrage du serveur de notifications push PickMe...")
    server = PushNotificationServer()
    server.listen_for_notifications()