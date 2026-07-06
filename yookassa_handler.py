import uuid
import requests
from config import YOOKASSA_SHOP_ID, YOOKASSA_SECRET
from database import SessionLocal, Purchase, User
from datetime import datetime, timedelta

class YooKassa:
    def __init__(self):
        self.shop_id = YOOKASSA_SHOP_ID
        self.secret = YOOKASSA_SECRET
        self.url = "https://api.yookassa.ru/v3/payments"

    def _auth(self):
        import base64
        return base64.b64encode(f"{self.shop_id}:{self.secret}".encode()).decode()

    def create_payment(self, user_id, amount, description, metadata):
        idempotence = str(uuid.uuid4())
        headers = {
            "Authorization": f"Basic {self._auth()}",
            "Content-Type": "application/json",
            "Idempotence-Key": idempotence
        }
        payload = {
            "amount": {"value": f"{amount:.2f}", "currency": "RUB"},
            "payment_method_data": {"type": "bank_card"},
            "confirmation": {
                "type": "redirect",
                "return_url": "https://t.me/YourBotName"
            },
            "description": description,
            "metadata": metadata
        }
        r = requests.post(self.url, json=payload, headers=headers)
        return r.json()

    def check_payment(self, payment_id):
        headers = {"Authorization": f"Basic {self._auth()}"}
        r = requests.get(f"{self.url}/{payment_id}", headers=headers)
        return r.json()

    def apply_payment(self, payment_id, db):
        data = self.check_payment(payment_id)
        if data.get("status") != "succeeded":
            return False
        meta = data.get("metadata", {})
        user_id = int(meta.get("user_id"))
        item_type = meta.get("item_type")
        item_id = meta.get("item_id")

        purchase = db.query(Purchase).filter_by(payment_id=payment_id).first()
        if not purchase or purchase.status == "completed":
            return False

        user = db.query(User).filter_by(telegram_id=user_id).first()
        if not user:
            return False

        # начисление
        if item_type == "subscription":
            days = {"day": 1, "week": 7, "month": 30}.get(item_id, 1)
            now = datetime.utcnow()
            user.sub_end = (user.sub_end or now) + timedelta(days=days)
            user.is_subscribed = True
            user.st += {"day": 10, "week": 50, "month": 250}.get(item_id, 0)

        elif item_type == "tasks":
            rewards = {"task_1": 1, "task_3": 3, "task_10": 8}
            user.st += rewards.get(item_id, 0)

        purchase.status = "completed"
        db.commit()
        return True

yookassa = YooKassa()