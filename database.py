from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import DATABASE_URL

Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)
    username = Column(String(255))
    first_name = Column(String(255))
    
    # Ресурсы
    knowledge_points = Column(Integer, default=0)  # KP
    scholar_thoughts = Column(Integer, default=0)  # ST
    
    # Игровые параметры
    school = Column(String(255))
    city = Column(String(255))
    level = Column(Integer, default=1)
    
    # Улучшения
    class_teacher_level = Column(Integer, default=0)
    notebooks_level = Column(Integer, default=0)
    chemistry_level = Column(Integer, default=0)
    
    # Прокачка
    attack_speed = Column(Float, default=1.0)  # тапов в секунду
    tap_power = Column(Integer, default=1)  # KP за тап
    
    # Статистика
    total_taps = Column(Integer, default=0)
    total_battles = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    win_streak = Column(Integer, default=0)
    max_streak = Column(Integer, default=0)
    
    # Достижения
    last_login = Column(DateTime)
    login_streak = Column(Integer, default=0)
    last_streak_update = Column(DateTime)
    
    # Подписки
    subscription_end = Column(DateTime)
    is_subscribed = Column(Boolean, default=False)
    
    # Настройки
    selected_avatar = Column(String(255), default="default")
    selected_background = Column(String(255), default="classroom")
    nickname_color = Column(String(255), default="#FFFFFF")
    
    created_at = Column(DateTime, default=datetime.utcnow)

class Purchase(Base):
    __tablename__ = "purchases"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    item_type = Column(String(50))  # 'subscription', 'tasks', 'thoughts'
    item_id = Column(String(50))
    amount = Column(Integer)
    payment_id = Column(String(255))
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)

class Battle(Base):
    __tablename__ = "battles"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    bot_level = Column(Integer)
    user_score = Column(Integer)
    bot_score = Column(Integer)
    winner = Column(String(50))  # 'user', 'bot'
    duration = Column(Integer)  # в секундах
    created_at = Column(DateTime, default=datetime.utcnow)

class Achievement(Base):
    __tablename__ = "achievements"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    achievement_type = Column(String(50))
    level = Column(Integer, default=1)
    progress = Column(Integer, default=0)
    completed = Column(Boolean, default=False)
    claimed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
