import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN       = os.getenv("BOT_TOKEN")
WEB_APP_URL     = os.getenv("WEB_APP_URL", "https://ваш-сайт.onrender.com")
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")
YOOKASSA_SECRET = os.getenv("YOOKASSA_SECRET")
DATABASE_URL    = os.getenv("DATABASE_URL", "sqlite:///data.db")