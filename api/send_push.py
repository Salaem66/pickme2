#!/usr/bin/env python3
"""
API endpoint pour envoyer des notifications push
Appelé depuis le frontend quand l'admin envoie une notification
"""

from http.server import BaseHTTPRequestHandler
import json
import os
from typing import List, Dict, Any

try:
    from pywebpush import webpush, WebPushException
    from supabase import create_client, Client
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    print(f"Dependencies not available: {e}")
    DEPENDENCIES_AVAILABLE = False

class PushSender:
    def __init__(self):
        if not DEPENDENCIES_AVAILABLE:
            return

        # Configuration Supabase
        self.supabase_url = "https://utzflwmghpojlsthyuqf.supabase.co"
        self.supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV0emZsd21naHBvamxzdGh5dXFmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc1NDQxOTAsImV4cCI6MjA3MzEyMDE5MH0.j5qMspjG6FTN69DPwI0otqjw7Yp5lbbFadflpkjNvYc"
        self.supabase = create_client(self.supabase_url, self.supabase_key)

        # Clés VAPID pour les notifications push
        self.vapid_private_key = """-----BEGIN PRIVATE KEY-----
MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQg0gQELt1N4oZGH2YC
rQP9LRm1O6iYxNxrUNZEw8x7LaqhRANCAASeKXpHAw5N2XPgdCBKtaYJJKyPsY7X
6xNVfOd8p6dGFpXGkYtJ0TzQ2iAKpF1LzPL4Y5BqNzrW8HzRk2V9nQRm
-----END PRIVATE KEY-----"""
        self.vapid_public_key = "BJ4pekcDDk3Zc-B0IEq1pgkkrI-xjtfrE1V853ynp0YWlcaRi0nRPNDaIAqkXUvM8vhjkGo3OtbwfNGTZX2dBGY"
        self.vapid_email = "mael.sivenboren@gmail.com"

    def get_all_subscriptions(self) -> List[Dict]:
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

            # Construire le payload de notification
            payload = {
                "title": f"📢 PickMe",
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

            # Envoyer la notification push
            webpush(
                subscription_info=subscription_info,
                data=json.dumps(payload),
                vapid_private_key=self.vapid_private_key,
                vapid_claims={
                    "sub": f"mailto:{self.vapid_email}",
                }
            )

            print(f"✅ Push envoyée à {subscription_data['user_id']}")

            # Enregistrer la livraison
            try:
                self.supabase.table('notification_deliveries').insert({
                    'notification_id': notification['id'],
                    'user_id': subscription_data['user_id']
                }).execute()
            except Exception as e:
                print(f"Erreur enregistrement livraison: {e}")

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

    def broadcast_notification(self, notification: Dict):
        """Diffuse une notification à tous les abonnements actifs"""
        if not DEPENDENCIES_AVAILABLE:
            return {"success": False, "error": "Dependencies not available"}

        print(f"📢 Broadcasting notification: {notification['message']}")

        subscriptions = self.get_all_subscriptions()
        print(f"📱 {len(subscriptions)} abonnements trouvés")

        if not subscriptions:
            return {"success": True, "sent": 0, "total": 0, "message": "Aucun abonnement actif"}

        success_count = 0
        for subscription in subscriptions:
            if self.send_push_to_subscription(subscription, notification):
                success_count += 1

        return {
            "success": True,
            "sent": success_count,
            "total": len(subscriptions),
            "message": f"{success_count}/{len(subscriptions)} notifications envoyées"
        }

# Instance globale
push_sender = None

def get_push_sender():
    global push_sender
    if push_sender is None:
        push_sender = PushSender()
    return push_sender

class handler(BaseHTTPRequestHandler):
    """Handler pour l'API de notifications push"""

    def do_POST(self):
        """Handle POST requests pour envoyer des notifications push"""
        try:
            # Lire le body de la requête
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)

            try:
                data = json.loads(post_data.decode('utf-8'))
            except json.JSONDecodeError:
                self.send_error_response(400, "Invalid JSON in request body")
                return

            # Vérifier que l'utilisateur est admin
            if not data.get('is_admin', False):
                self.send_error_response(403, "Admin access required")
                return

            # Récupérer les données de notification
            notification = data.get('notification')
            if not notification:
                self.send_error_response(400, "Missing notification data")
                return

            # Envoyer les notifications push
            sender = get_push_sender()
            result = sender.broadcast_notification(notification)

            # Réponse JSON
            self.send_json_response(result)

        except Exception as e:
            print(f"Error in POST handler: {e}")
            self.send_error_response(500, f"Internal server error: {str(e)}")

    def send_json_response(self, data: dict, status_code: int = 200):
        """Envoie une réponse JSON"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

        response_json = json.dumps(data, ensure_ascii=False, indent=2)
        self.wfile.write(response_json.encode('utf-8'))

    def send_error_response(self, status_code: int, message: str):
        """Envoie une réponse d'erreur JSON"""
        self.send_json_response({
            "success": False,
            "error": True,
            "message": message,
            "status_code": status_code
        }, status_code)

    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()