#!/usr/bin/env python3
"""
Générateur de clés VAPID pour les notifications push
"""

from py_vapid import Vapid
import base64

def generate_vapid_keys():
    vapid = Vapid()
    vapid.generate_keys()

    # Récupérer les clés au bon format
    private_key = vapid.private_pem()
    public_key = vapid.public_key()

    print("🔑 Clés VAPID générées:")
    print(f"VAPID_PRIVATE_KEY={private_key.decode()}")
    print(f"VAPID_PUBLIC_KEY={public_key.decode()}")

    return private_key, public_key

if __name__ == "__main__":
    generate_vapid_keys()