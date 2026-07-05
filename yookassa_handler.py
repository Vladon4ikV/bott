import uuid
import requests
from datetime import datetime, timedelta
from config import YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY
from database import SessionLocal, User, Purchase
from sqlalchemy.orm import Session

class YooKassaHandler:
    def __init__(self):
        self.shop_id = YOOKASSA_SHOP_ID
        self.secret_key = YOOKASSA_SECRET_KEY
        self.api_url = "https://api.yookassa.ru/v3/payments"
    
    def create_payment(self, user_id: int, amount: float, description: str, 
                      metadata: dict = None) -> dict:
        """Создание платежа в ЮKassa"""
        idempotence_key = str(uuid.uuid4())
        
        headers = {
            "Authorization": f"Basic {self._get_auth()}",
            "Content-Type": "application/json",
            "Idempotence-Key": idempotence_key
        }
        
        data = {
            "amount": {
                "value": str(amount),
                "currency": "RUB"
            },
            "payment_method_data": {
                "type": "bank_card"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": f"https://t.me/YourBotName"
            },
            "description": description,
            "metadata": metadata or {}
        }
        
        response = requests.post(self.api_url, json=data, headers=headers)
        return response.json()
    
    def check_payment(self, payment_id: str) -> dict:
        """Проверка статуса платежа"""
        headers = {
            "Authorization": f"Basic {self._get_auth()}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(f"{self.api_url}/{payment_id}", headers=headers)
        return response.json()
    
    def _get_auth(self):
        import base64
        auth_string = f"{self.shop_id}:{self.secret_key}"
        return base64.b64encode(auth_string.encode()).decode()
    
    def process_payment(self, payment_id: str, db: Session):
        """Обработка успешного платежа"""
        payment_data = self.check_payment(payment_id)
        
        if payment_data.get("status") == "succeeded":
            metadata = payment_data.get("metadata", {})
            user_id = int(metadata.get("user_id"))
            item_type = metadata.get("item_type")
            item_id = metadata.get("item_id")
            
            # Находим покупку
            purchase = db.query(Purchase).filter(
                Purchase.payment_id == payment_id
            ).first()
            
            if purchase and purchase.status != "completed":
                purchase.status = "completed"
                
                # Начисляем награду
                user = db.query(User).filter(User.telegram_id == user_id).first()
                if user:
                    self._apply_reward(user, item_type, item_id, db)
                
                db.commit()
                return True
        return False
    
    def _apply_reward(self, user: User, item_type: str, item_id: str, db: Session):
        """Начисление награды за покупку"""
        
        # Маппинг: сколько мыслей ученого за покупку
        thoughts_rewards = {
            "task_1": 1,
            "task_3": 3,
            "task_10": 8,
            "day": 10,
            "week": 50,
            "month": 250
        }
        
        if item_type == "subscription":
            # Подписка
            days_map = {"day": 1, "week": 7, "month": 30}
            days = days_map.get(item_id, 1)
            
            # Начисляем мысли ученого
            if item_id in thoughts_rewards:
                user.scholar_thoughts += thoughts_rewards[item_id]
            
            # Продлеваем подписку
            if user.subscription_end and user.subscription_end > datetime.utcnow():
                user.subscription_end += timedelta(days=days)
            else:
                user.subscription_end = datetime.utcnow() + timedelta(days=days)
            
            user.is_subscribed = True
            
        elif item_type == "tasks":
            # Покупка задач
            if item_id in thoughts_rewards:
                user.scholar_thoughts += thoughts_rewards[item_id]
                user.knowledge_points += int(thoughts_rewards[item_id] * 10)  # Бонус KP