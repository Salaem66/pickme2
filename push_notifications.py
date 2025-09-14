#!/usr/bin/env python3
"""
Module de notifications push intégré au serveur principal
Compatible Railway avec gestion des dépendances
"""

import json
import asyncio
from typing import List, Dict, Any, Optional

# Import conditionnel pour éviter les erreurs si pas installé
try:
    from pywebpush import webpush, WebPushException
    from supabase import create_client
    PUSH_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Push dependencies not available: {e}")
    PUSH_AVAILABLE = False

class PushNotificationManager:
    def __init__(self):
        if not PUSH_AVAILABLE:
            print("⚠️ Push notifications disabled - dependencies not found")
            return

        # Configuration Supabase
        self.supabase_url = "https://utzflwmghpojlsthyuqf.supabase.co"
        self.supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV0emZsd21naHBvamxzdGh5dXFmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc1NDQxOTAsImV4cCI6MjA3MzEyMDE5MH0.j5qMspjG6FTN69DPwI0otqjw7Yp5lbbFadflpkjNvYc"

        try:
            self.supabase = create_client(self.supabase_url, self.supabase_key)
        except Exception as e:
            print(f"⚠️ Supabase connection failed: {e}")
            self.supabase = None

        # Clés VAPID pour notifications push
        self.vapid_private_key = """-----BEGIN PRIVATE KEY-----
MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQg0gQELt1N4oZGH2YC
rQP9LRm1O6iYxNxrUNZEw8x7LaqhRANCAASeKXpHAw5N2XPgdCBKtaYJJKyPsY7X
6xNVfOd8p6dGFpXGkYtJ0TzQ2iAKpF1LzPL4Y5BqNzrW8HzRk2V9nQRm
-----END PRIVATE KEY-----"""

        self.vapid_public_key = "BJ4pekcDDk3Zc-B0IEq1pgkkrI-xjtfrE1V853ynp0YWlcaRi0nRPNDaIAqkXUvM8vhjkGo3OtbwfNGTZX2dBGY"
        self.vapid_email = "mael.sivenboren@gmail.com"

    def is_available(self) -> bool:
        """Vérifie si les notifications push sont disponibles"""
        return PUSH_AVAILABLE and self.supabase is not None

    async def get_active_subscriptions(self) -> List[Dict]:
        """Récupère tous les abonnements push actifs"""
        if not self.is_available():
            return []

        try:
            response = self.supabase.table('push_subscriptions').select('*').eq('is_active', True).execute()
            return response.data or []
        except Exception as e:
            print(f"❌ Error fetching subscriptions: {e}")
            return []

    async def send_push_to_device(self, subscription: Dict, notification: Dict) -> bool:
        """Envoie une notification push à un appareil spécifique"""
        if not self.is_available():
            return False

        try:
            subscription_info = {
                "endpoint": subscription['endpoint'],
                "keys": {
                    "p256dh": subscription['p256dh'],
                    "auth": subscription['auth']
                }
            }

            # Payload optimisé pour la rétention
            payload = {
                "title": "🎬 PickMe",
                "body": notification['message'],
                "icon": "/pickme_logo.png",
                "badge": "/pickme_logo.png",
                "tag": f"admin-{notification['id']}",
                "requireInteraction": True,
                "actions": [
                    {
                        "action": "open",
                        "title": "Voir l'app",
                        "icon": "/pickme_logo.png"
                    }
                ],
                "data": {
                    "url": "/",
                    "notificationId": notification['id'],
                    "timestamp": notification.get('created_at')
                }
            }

            # Envoyer via WebPush
            webpush(
                subscription_info=subscription_info,
                data=json.dumps(payload),
                vapid_private_key=self.vapid_private_key,
                vapid_claims={
                    "sub": f"mailto:{self.vapid_email}",
                }
            )

            # Enregistrer la livraison pour analytics
            try:
                self.supabase.table('notification_deliveries').insert({
                    'notification_id': notification['id'],
                    'user_id': subscription['user_id']
                }).execute()
            except Exception as e:
                print(f"⚠️ Failed to log delivery: {e}")

            print(f"✅ Push sent to user {subscription['user_id']}")
            return True

        except WebPushException as e:
            print(f"❌ WebPush error: {e}")
            # Désactiver les abonnements expirés
            if e.response and e.response.status_code in [410, 404, 413]:
                await self.deactivate_subscription(subscription['id'])
            return False

        except Exception as e:
            print(f"❌ Push send error: {e}")
            return False

    async def deactivate_subscription(self, subscription_id: str):
        """Désactive un abonnement expiré"""
        if not self.supabase:
            return

        try:
            self.supabase.table('push_subscriptions').update({
                'is_active': False
            }).eq('id', subscription_id).execute()
            print(f"🗑️ Deactivated expired subscription {subscription_id}")
        except Exception as e:
            print(f"⚠️ Failed to deactivate subscription: {e}")

    async def broadcast_notification(self, notification: Dict) -> Dict[str, Any]:
        """Diffuse une notification à tous les abonnés actifs"""
        if not self.is_available():
            return {
                "success": False,
                "error": "Push notifications not available",
                "sent": 0,
                "total": 0
            }

        print(f"📢 Broadcasting push notification: {notification['message']}")

        # Récupérer tous les abonnements actifs
        subscriptions = await self.get_active_subscriptions()
        total_subscriptions = len(subscriptions)

        print(f"📱 Found {total_subscriptions} active subscriptions")

        if total_subscriptions == 0:
            return {
                "success": True,
                "message": "No active subscriptions found",
                "sent": 0,
                "total": 0
            }

        # Envoyer les notifications en parallèle pour performance
        tasks = []
        for subscription in subscriptions:
            task = self.send_push_to_device(subscription, notification)
            tasks.append(task)

        # Attendre toutes les notifications
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Compter les succès
        successful_sends = sum(1 for result in results if result is True)

        print(f"✅ Successfully sent {successful_sends}/{total_subscriptions} push notifications")

        return {
            "success": True,
            "message": f"Sent {successful_sends}/{total_subscriptions} push notifications",
            "sent": successful_sends,
            "total": total_subscriptions,
            "success_rate": f"{(successful_sends/total_subscriptions*100):.1f}%" if total_subscriptions > 0 else "0%"
        }

# Instance globale pour réutilisation
_push_manager = None

def get_push_manager() -> PushNotificationManager:
    """Singleton pour le gestionnaire de notifications push"""
    global _push_manager
    if _push_manager is None:
        _push_manager = PushNotificationManager()
    return _push_manager

# Fonction utilitaire pour intégration dans FastAPI
async def send_admin_notification_push(notification_data: Dict) -> Dict[str, Any]:
    """
    Fonction d'API pour envoyer des notifications push
    À appeler depuis le serveur principal
    """
    manager = get_push_manager()

    if not manager.is_available():
        return {
            "success": False,
            "error": "Push notification service unavailable",
            "message": "Dependencies not installed or configuration missing"
        }

    return await manager.broadcast_notification(notification_data)

if __name__ == "__main__":
    # Test du système
    async def test_push():
        manager = get_push_manager()
        if manager.is_available():
            print("🧪 Testing push notification system...")

            test_notification = {
                "id": "test-123",
                "message": "Test de notification push PickMe !",
                "type": "info",
                "created_at": "2024-01-01T00:00:00Z"
            }

            result = await manager.broadcast_notification(test_notification)
            print(f"📊 Test result: {result}")
        else:
            print("❌ Push system not available for testing")

    asyncio.run(test_push())