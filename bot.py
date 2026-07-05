import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup  # ← ПРАВИЛЬНО!
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from config import BOT_TOKEN, WEB_APP_URL
from database import get_db, User, Purchase, Achievement
from yookassa_handler import YooKassaHandler

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
yookassa = YooKassaHandler()

# Состояния
class Registration(StatesGroup):
    waiting_for_school = State()
    waiting_for_city = State()

class BattleStates(StatesGroup):
    in_battle = State()

# Клавиатуры
def main_keyboard(user: User):
    """Главная клавиатура"""
    kb = [
        [
            InlineKeyboardButton(
                text="🏫 Играть",
                web_app=WebAppInfo(url=WEB_APP_URL)
            )
        ],
        [
            InlineKeyboardButton(text="⚔️ Баттл", callback_data="battle"),
            InlineKeyboardButton(text="📊 Рейтинг", callback_data="rating")
        ],
        [
            InlineKeyboardButton(text="🎯 Ежедневные комбо", callback_data="daily"),
            InlineKeyboardButton(text="🎡 Рулетка", callback_data="roulette")
        ],
        [
            InlineKeyboardButton(text="💎 Магазин", callback_data="shop"),
            InlineKeyboardButton(text="📖 Улучшения", callback_data="upgrades")
        ],
        [
            InlineKeyboardButton(text="📈 Статистика", callback_data="stats"),
            InlineKeyboardButton(text="🎁 Достижения", callback_data="achievements")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    db = next(get_db())
    user = db.query(User).filter(User.telegram_id == message.from_user.id).first()
    
    if not user:
        # Новый пользователь
        await message.answer(
            "🎓 Добро пожаловать в Школьный Баттл!\n\n"
            "Давай познакомимся! Сначала укажи свою школу:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏫 Школа №1", callback_data="school_1")],
                [InlineKeyboardButton(text="🏫 Школа №2", callback_data="school_2")],
                [InlineKeyboardButton(text="🏫 Школа №3", callback_data="school_3")],
                [InlineKeyboardButton(text="✏️ Ввести вручную", callback_data="school_manual")]
            ])
        )
        await state.set_state(Registration.waiting_for_school)
    else:
        # Проверяем ежедневный вход
        await check_daily_login(user, db)
        
        await message.answer(
            f"🎓 С возвращением, {user.first_name}!\n"
            f"📚 Очки знаний: {user.knowledge_points}\n"
            f"🧠 Мысли ученого: {user.scholar_thoughts}\n"
            f"🏆 Уровень: {user.level}",
            reply_markup=main_keyboard(user)
        )

@dp.callback_query(StateFilter(Registration.waiting_for_school))
async def process_school(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "school_manual":
        await callback.message.answer("✏️ Введи название своей школы:")
        return
    
    school = callback.data.replace("school_", "")
    await state.update_data(school=school)
    
    await callback.message.answer(
        "🌆 Теперь укажи свой город:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🌆 Москва", callback_data="city_moscow")],
            [InlineKeyboardButton(text="🌆 Санкт-Петербург", callback_data="city_spb")],
            [InlineKeyboardButton(text="🌆 Новосибирск", callback_data="city_nsk")],
            [InlineKeyboardButton(text="✏️ Ввести вручную", callback_data="city_manual")]
        ])
    )
    await state.set_state(Registration.waiting_for_city)

@dp.callback_query(StateFilter(Registration.waiting_for_city))
async def process_city(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    school = data.get("school")
    
    if callback.data == "city_manual":
        await callback.message.answer("✏️ Введи название своего города:")
        return
    
    city = callback.data.replace("city_", "")
    
    # Создаем пользователя
    db = next(get_db())
    user = User(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
        school=school,
        city=city
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    await callback.message.answer(
        f"✅ Отлично! Ты зачислен в {school}, г. {city}!\n\n"
        "🎓 Начинай свое приключение!",
        reply_markup=main_keyboard(user)
    )
    await state.clear()

@dp.callback_query(lambda c: c.data == "daily")
async def daily_combo(callback: types.CallbackQuery):
    db = next(get_db())
    user = db.query(User).filter(User.telegram_id == callback.from_user.id).first()
    
    # Проверяем, может ли игрок получить комбо
    today = datetime.utcnow().date()
    
    # Нужно набрать 10000 KP за сегодня
    if user.knowledge_points >= 10000:
        # Начисляем бонус
        user.knowledge_points += 5000
        db.commit()
        await callback.answer("🎉 Комбо выполнено! +5000 KP", show_alert=True)
    else:
        await callback.answer(
            f"📚 Нужно набрать 10000 KP сегодня.\n"
            f"У тебя: {user.knowledge_points} KP",
            show_alert=True
        )

@dp.callback_query(lambda c: c.data == "roulette")
async def roulette(callback: types.CallbackQuery):
    db = next(get_db())
    user = db.query(User).filter(User.telegram_id == callback.from_user.id).first()
    
    if user.knowledge_points < 1000:
        await callback.answer("❌ Нужно 1000 KP для рулетки!", show_alert=True)
        return
    
    # Список наград с весами
    rewards = [
        (10, 30),    # 30% шанс
        (50, 25),    # 25% шанс
        (150, 20),   # 20% шанс
        (300, 15),   # 15% шанс
        (500, 7),    # 7% шанс
        (1000, 2),   # 2% шанс
        (2500, 0.5), # 0.5% шанс
        (10000, 0.1) # 0.1% шанс
    ]
    
    import random
    total_weight = sum(w for _, w in rewards)
    roll = random.random() * total_weight
    
    cumulative = 0
    reward = 10  # по умолчанию
    
    for value, weight in rewards:
        cumulative += weight
        if roll <= cumulative:
            reward = value
            break
    
    # Особый приз - 1 месяц подписки (шанс 1 на миллиард)
    if random.random() < 0.000000001:
        reward = "telegram_premium"
    
    # Списываем 1000 KP
    user.knowledge_points -= 1000
    
    # Начисляем награду
    if reward == "telegram_premium":
        user.knowledge_points += 10000  # Бонус
        await callback.answer(
            "🎉🎉🎉 ПОЗДРАВЛЯЕМ!\n"
            "Ты выиграл Telegram Premium на 1 месяц!\n"
            "Сделай скриншот и напиши администраторам!",
            show_alert=True
        )
    else:
        user.knowledge_points += reward
        db.commit()
        
        # Визуализация с эмодзи
        emoji = "🎉" if reward >= 500 else "✨" if reward >= 100 else "🎯"
        await callback.answer(f"{emoji} Ты выиграл {reward} KP!", show_alert=True)

async def check_daily_login(user: User, db: Session):
    """Проверка ежедневного входа"""
    today = datetime.utcnow().date()
    
    if user.last_login:
        last_date = user.last_login.date()
        if last_date == today:
            return  # Уже заходил сегодня
        
        if last_date == today - timedelta(days=1):
            # Подряд
            user.login_streak += 1
        else:
            # Сброс
            user.login_streak = 1
    else:
        user.login_streak = 1
    
    user.last_login = datetime.utcnow()
    
    # Награды за вход
    if user.login_streak == 3:
        user.knowledge_points += 100
        # Отправляем уведомление
    elif user.login_streak == 7:
        user.scholar_thoughts += 2
    elif user.login_streak == 14:
        user.knowledge_points += 1000
    elif user.login_streak == 30:
        user.knowledge_points += 5000
        # VIP бонус
    
    db.commit()

# ... остальные обработчики (battle, shop, upgrades, stats)

if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
