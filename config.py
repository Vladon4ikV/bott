import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# ЮKassa
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY")

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///school_bot.db")

# Web App
WEB_APP_URL = os.getenv("WEB_APP_URL", "https://your-domain.com")