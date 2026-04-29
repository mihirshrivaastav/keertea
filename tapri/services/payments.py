import json
import urllib.error
import urllib.parse
import urllib.request
from base64 import b64encode

from flask import current_app


def normalize_payment_method(value):
    payment_method = (value or "").strip().lower()
    allowed = {
        "cash on delivery": ("manual", "pending"),
        "upi / gpay / phonepe": ("razorpay", "pending"),
        "credit / debit card": ("stripe", "pending"),
        "net banking": ("razorpay", "pending"),
    }
    return allowed.get(payment_method, ("manual", "pending"))


def call_payment_provider(provider, amount_rupees, order_id, customer_name):
    if provider == "manual":
        return {"status": "pending", "reference": f"COD-{order_id}", "message": "Cash on delivery selected."}

    amount_paise = int(round(amount_rupees * 100))
    if provider == "stripe":
        secret = current_app.config.get("STRIPE_SECRET_KEY")
        if not secret:
            raise ValueError("Stripe is not configured. Set STRIPE_SECRET_KEY to enable card payments.")
        payload = urllib.parse.urlencode(
            {
                "amount": amount_paise,
                "currency": "inr",
                "description": f"KeerTea order #{order_id} for {customer_name}",
                "metadata[order_id]": order_id,
            }
        ).encode()
        request_obj = urllib.request.Request(
            "https://api.stripe.com/v1/payment_intents",
            data=payload,
            method="POST",
            headers={
                "Authorization": f"Bearer {secret}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        with urllib.request.urlopen(request_obj, timeout=20) as response:
            body = json.loads(response.read().decode())
        return {
            "status": body.get("status", "requires_payment_method"),
            "reference": body["id"],
            "clientSecret": body.get("client_secret"),
            "message": "Stripe payment intent created.",
        }

    if provider == "razorpay":
        key_id = current_app.config.get("RAZORPAY_KEY_ID")
        key_secret = current_app.config.get("RAZORPAY_KEY_SECRET")
        if not key_id or not key_secret:
            raise ValueError("Razorpay is not configured. Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET.")
        payload = json.dumps(
            {
                "amount": amount_paise,
                "currency": "INR",
                "receipt": f"keertea-{order_id}",
                "notes": {"customer_name": customer_name},
            }
        ).encode()
        auth = b64encode(f"{key_id}:{key_secret}".encode()).decode()
        request_obj = urllib.request.Request(
            "https://api.razorpay.com/v1/orders",
            data=payload,
            method="POST",
            headers={
                "Authorization": f"Basic {auth}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(request_obj, timeout=20) as response:
            body = json.loads(response.read().decode())
        return {
            "status": body.get("status", "created"),
            "reference": body["id"],
            "keyId": key_id,
            "amount": body.get("amount"),
            "message": "Razorpay order created.",
        }

    raise ValueError("Unsupported payment provider.")

