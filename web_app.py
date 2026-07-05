from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import json
from datetime import datetime
from database import SessionLocal, User
from sqlalchemy.orm import Session

app = Flask(__name__)
app.secret_key = "your-secret-key"
CORS(app)

@app.route("/")
def index():
    return render_template("game.html")

@app.route("/api/user/<int:telegram_id>")
def get_user(telegram_id):
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    db.close()
    
    if user:
        return jsonify({
            "id": user.id,
            "knowledge_points": user.knowledge_points,
            "scholar_thoughts": user.scholar_thoughts,
            "level": user.level,
            "attack_speed": user.attack_speed,
            "tap_power": user.tap_power,
            "school": user.school,
            "city": user.city
        })
    return jsonify({"error": "User not found"}), 404

@app.route("/api/tap", methods=["POST"])
def handle_tap():
    data = request.json
    telegram_id = data.get("telegram_id")
    
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    
    if user:
        # Начисляем KP
        user.knowledge_points += user.tap_power
        user.total_taps += 1
        
        # Проверяем уровень
        new_level = user.knowledge_points // 1000 + 1
        if new_level > user.level:
            user.level = new_level
            user.scholar_thoughts += 1
        
        db.commit()
        db.refresh(user)
        
        db.close()
        return jsonify({
            "knowledge_points": user.knowledge_points,
            "scholar_thoughts": user.scholar_thoughts,
            "level": user.level,
            "tap_power": user.tap_power
        })
    
    db.close()
    return jsonify({"error": "User not found"}), 404

# Остальные API эндпоинты для баттлов, магазина, улучшений

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)