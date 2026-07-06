from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from config import DATABASE_URL

Base = declarative_base()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, index=True)
    username = Column(String)
    first_name = Column(String)
    school = Column(String)
    city = Column(String)
    kp = Column(Integer, default=0)
    st = Column(Integer, default=0)
    level = Column(Integer, default=1)
    taps = Column(Integer, default=0)
    login_streak = Column(Integer, default=0)
    last_login = Column(DateTime, default=datetime.utcnow)
    battle_wins = Column(Integer, default=0)
    battle_losses = Column(Integer, default=0)
    avatar = Column(String, default="default")
    is_subscribed = Column(Boolean, default=False)
    sub_end = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Purchase(Base):
    __tablename__ = "purchases"
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, index=True)
    item_type = Column(String)
    item_id = Column(String)
    amount = Column(Integer)
    payment_id = Column(String, unique=True)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()