# web_app.py
import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
from database import SessionLocal, User, Purchase
from sqlalchemy.orm import Session

app = Flask(__name__)
CORS(app)

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

def get_user_db(telegram_id: int) -> User | None:
    """Получить пользователя из БД"""
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    db.close()
    return user

def update_user_db(telegram_id: int, data: dict) -> dict:
    """Обновить данные пользователя"""
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        db.close()
        return {"error": "User not found"}
    
    for key, value in data.items():
        if hasattr(user, key):
            setattr(user, key, value)
    
    # Проверка уровня
    new_level = user.kp // 100 + 1
    if new_level > user.level:
        user.level = new_level
    
    db.commit()
    db.refresh(user)
    db.close()
    
    return {
        "kp": user.kp,
        "st": user.st,
        "level": user.level,
        "taps": user.taps,
        "login_streak": user.login_streak
    }

# ==================== API ЭНДПОИНТЫ ====================

@app.route("/")
def home():
    return "🤖 Школьный Баттл API работает!", 200

@app.route("/health")
def health():
    return {"status": "ok", "time": datetime.now().isoformat()}, 200

@app.route("/api/user/<int:telegram_id>", methods=["GET"])
def get_user_data(telegram_id: int):
    """Получить данные пользователя для Web App"""
    user = get_user_db(telegram_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify({
        "kp": user.kp,
        "st": user.st,
        "level": user.level,
        "taps": user.taps,
        "login_streak": user.login_streak,
        "school": user.school,
        "city": user.city,
        "avatar": user.avatar,
        "is_subscribed": user.is_subscribed,
        "battle_wins": user.battle_wins,
        "battle_losses": user.battle_losses
    })

@app.route("/api/tap", methods=["POST"])
def handle_tap():
    """Обработка тапа из Web App"""
    data = request.json
    telegram_id = data.get("user_id")
    
    if not telegram_id:
        return jsonify({"error": "user_id required"}), 400
    
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    
    if not user:
        db.close()
        return jsonify({"error": "User not found"}), 404
    
    # Начисляем очки
    user.kp += 1
    user.taps += 1
    
    # Каждые 10 тапов — мысль ученого
    if user.taps % 10 == 0:
        user.st += 1
    
    # Проверка уровня
    new_level = user.kp // 100 + 1
    if new_level > user.level:
        user.level = new_level
    
    db.commit()
    db.refresh(user)
    db.close()
    
    return jsonify({
        "kp": user.kp,
        "st": user.st,
        "level": user.level,
        "taps": user.taps
    })

@app.route("/api/bonus", methods=["POST"])
def handle_bonus():
    """Ежедневный бонус из Web App"""
    data = request.json
    telegram_id = data.get("user_id")
    
    if not telegram_id:
        return jsonify({"error": "user_id required"}), 400
    
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    
    if not user:
        db.close()
        return jsonify({"error": "User not found"}), 404
    
    # Проверяем, получал ли бонус сегодня
    today = datetime.now().date().isoformat()
    last_bonus = getattr(user, "last_bonus", "")
    
    if last_bonus == today:
        db.close()
        return jsonify({"error": "Already claimed today", "kp": user.kp}), 400
    
    # Начисляем бонус
    bonus = 50 + user.login_streak * 5
    user.kp += bonus
    user.last_bonus = today
    
    db.commit()
    db.refresh(user)
    db.close()
    
    return jsonify({
        "kp": user.kp,
        "bonus": bonus,
        "login_streak": user.login_streak
    })

@app.route("/api/battle", methods=["POST"])
def handle_battle():
    """Результат баттла из Web App"""
    data = request.json
    telegram_id = data.get("user_id")
    win = data.get("win", False)
    difficulty = data.get("difficulty", "easy")
    
    if not telegram_id:
        return jsonify({"error": "user_id required"}), 400
    
    rewards = {"easy": 90, "medium": 310, "hard": 500}
    
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    
    if not user:
        db.close()
        return jsonify({"error": "User not found"}), 404
    
    if win:
        user.kp += rewards.get(difficulty, 90)
        user.battle_wins += 1
    else:
        user.kp += 10
        user.battle_losses += 1
    
    db.commit()
    db.refresh(user)
    db.close()
    
    return jsonify({
        "kp": user.kp,
        "battle_wins": user.battle_wins,
        "battle_losses": user.battle_losses
    })

@app.route("/api/roulette", methods=["POST"])
def handle_roulette():
    """Рулетка из Web App"""
    import random
    data = request.json
    telegram_id = data.get("user_id")
    
    if not telegram_id:
        return jsonify({"error": "user_id required"}), 400
    
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    
    if not user:
        db.close()
        return jsonify({"error": "User not found"}), 404
    
    if user.kp < 1000:
        db.close()
        return jsonify({"error": "Not enough KP", "kp": user.kp}), 400
    
    # Списываем 1000
    user.kp -= 1000
    
    # Выигрыш
    rewards = [10, 50, 150, 300, 500, 1000, 2500, 5000]
    weights = [30, 25, 20, 15, 7, 2, 0.5, 0.1]
    win = random.choices(rewards, weights=weights)[0]
    
    # Особый приз (1 на миллион)
    if random.random() < 0.000001:
        win = "premium"
    
    if win == "premium":
        user.kp += 10000
        result = {"win": "premium", "message": "🎉 Telegram Premium на месяц!"}
    else:
        user.kp += win
        result = {"win": win, "message": f"🎉 {win} KP"}
    
    db.commit()
    db.refresh(user)
    db.close()
    
    return jsonify({
        "kp": user.kp,
        "result": result
    })

@app.route("/api/daily_combo", methods=["POST"])
def handle_daily_combo():
    """Ежедневное комбо (нужно 1000 тапов за день)"""
    data = request.json
    telegram_id = data.get("user_id")
    
    if not telegram_id:
        return jsonify({"error": "user_id required"}), 400
    
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    
    if not user:
        db.close()
        return jsonify({"error": "User not found"}), 404
    
    today = datetime.now().date().isoformat()
    last_combo = getattr(user, "last_combo", "")
    
    if last_combo == today:
        db.close()
        return jsonify({"error": "Already claimed today", "kp": user.kp}), 400
    
    # Проверяем, сколько тапов было сегодня (нужно 1000)
    # Для упрощения проверяем общее количество тапов (в реальности нужно хранить ежедневную статистику)
    if user.taps < 1000:
        db.close()
        return jsonify({"error": "Need 1000 taps today", "taps": user.taps}), 400
    
    user.kp += 5000
    user.last_combo = today
    
    db.commit()
    db.refresh(user)
    db.close()
    
    return jsonify({
        "kp": user.kp,
        "bonus": 5000,
        "message": "🎉 Комбо выполнено! +5000 KP"
    })

# ==================== ЗАПУСК ====================
if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)