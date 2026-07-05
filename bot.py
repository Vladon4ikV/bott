import asyncio
import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

# ==================== КОНФИГ ====================
BOT_TOKEN = "8224015269:AAHeZYvVzSZG_OexHc_lvtNMYq1k98Adhgw"
WEB_APP_URL = "https://school-bot-webapp.onrender.com"

# ==================== НАСТРОЙКА ====================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=storage)

# ==================== ДАННЫЕ В ПАМЯТИ ====================
users_data = {}

# ==================== СОСТОЯНИЯ ====================
class RegisterStates(StatesGroup):
    waiting_for_school = State()
    waiting_for_city = State()

# ==================== КЛАВИАТУРЫ ====================

def get_main_keyboard(user_id: int):
    """Главное меню (после регистрации)"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🎮 Запустить игру",
                web_app=WebAppInfo(url=WEB_APP_URL)
            )
        ],
        [
            InlineKeyboardButton(text="👆 Тапнуть", callback_data="tap"),
            InlineKeyboardButton(text="📊 Статистика", callback_data="stats")
        ],
        [
            InlineKeyboardButton(text="🏫 Сменить школу", callback_data="change_school"),
            InlineKeyboardButton(text="🎁 Бонус", callback_data="bonus")
        ],
        [
            InlineKeyboardButton(text="⚔️ Баттл", callback_data="battle"),
            InlineKeyboardButton(text="🎡 Рулетка", callback_data="roulette")
        ],
        [
            InlineKeyboardButton(text="💎 Магазин", callback_data="shop"),
            InlineKeyboardButton(text="📈 Рейтинг", callback_data="rating")
        ]
    ])

def get_school_keyboard():
    """Выбор школы"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏫 Школа №1", callback_data="school_1")],
        [InlineKeyboardButton(text="🏫 Школа №2", callback_data="school_2")],
        [InlineKeyboardButton(text="🏫 Школа №3", callback_data="school_3")],
        [InlineKeyboardButton(text="🏫 Школа №4", callback_data="school_4")],
        [InlineKeyboardButton(text="✏️ Ввести вручную", callback_data="school_manual")]
    ])

def get_city_keyboard():
    """Выбор города"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌆 Москва", callback_data="city_Москва")],
        [InlineKeyboardButton(text="🌆 Санкт-Петербург", callback_data="city_Санкт-Петербург")],
        [InlineKeyboardButton(text="🌆 Новосибирск", callback_data="city_Новосибирск")],
        [InlineKeyboardButton(text="🌆 Екатеринбург", callback_data="city_Екатеринбург")],
        [InlineKeyboardButton(text="🌆 Казань", callback_data="city_Казань")],
        [InlineKeyboardButton(text="✏️ Ввести вручную", callback_data="city_manual")]
    ])

# ==================== ОБРАБОТЧИКИ ====================

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    
    if user_id not in users_data:
        await message.answer(
            "🎓 Добро пожаловать в Школьный Баттл!\n\n"
            "Для начала выбери свою школу:",
            reply_markup=get_school_keyboard()
        )
        await state.set_state(RegisterStates.waiting_for_school)
        return
    
    user = users_data[user_id]
    
    await message.answer(
        f"🎓 Привет, {message.from_user.first_name}!\n"
        f"🏫 Школа: {user.get('school', 'Не выбрана')}\n"
        f"🌆 Город: {user.get('city', 'Не выбран')}\n"
        f"📚 Очки знаний: {user.get('kp', 0)}\n"
        f"🧠 Мысли ученого: {user.get('st', 0)}\n"
        f"🏆 Уровень: {user.get('level', 1)}\n\n"
        f"Выбери действие:",
        reply_markup=get_main_keyboard(user_id)
    )

@dp.callback_query(lambda c: c.data.startswith("school_"))
async def process_school(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора школы"""
    if callback.data == "school_manual":
        await callback.message.answer("✏️ Введи название своей школы:")
        await callback.answer()
        return
    
    school = callback.data.replace("school_", "")
    await state.update_data(school=f"Школа №{school}")
    
    await callback.message.edit_text(
        "🌆 Теперь выбери свой город:",
        reply_markup=get_city_keyboard()
    )
    await callback.answer()
    await state.set_state(RegisterStates.waiting_for_city)

@dp.message(RegisterStates.waiting_for_school)
async def process_school_manual(message: types.Message, state: FSMContext):
    """Ручной ввод школы"""
    school = message.text.strip()
    await state.update_data(school=school)
    
    await message.answer(
        "🌆 Теперь выбери свой город:",
        reply_markup=get_city_keyboard()
    )
    await state.set_state(RegisterStates.waiting_for_city)

@dp.callback_query(lambda c: c.data.startswith("city_"), RegisterStates.waiting_for_city)
async def process_city(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора города"""
    user_id = callback.from_user.id
    
    if callback.data == "city_manual":
        await callback.message.answer("✏️ Введи название своего города:")
        await callback.answer()
        return
    
    city = callback.data.replace("city_", "")
    data = await state.get_data()
    school = data.get("school", "Школа №1")
    
    # Регистрируем пользователя
    users_data[user_id] = {
        "school": school,
        "city": city,
        "kp": 0,
        "st": 0,
        "level": 1,
        "taps": 0,
        "login_streak": 1,
        "last_login": datetime.now().isoformat(),
        "battle_wins": 0,
        "battle_losses": 0
    }
    
    await callback.message.edit_text(
        f"✅ Отлично! Ты зачислен в {school}, г. {city}!\n\n"
        f"🎓 Теперь нажимай на школьника и зарабатывай очки знаний!\n"
        f"Начинай свое приключение! 🚀",
        reply_markup=get_main_keyboard(user_id)  # ← ВАЖНО! ПОКАЗЫВАЕМ ГЛАВНОЕ МЕНЮ
    )
    await callback.answer()
    await state.clear()

@dp.message(RegisterStates.waiting_for_city)
async def process_city_manual(message: types.Message, state: FSMContext):
    """Ручной ввод города"""
    user_id = message.from_user.id
    city = message.text.strip()
    data = await state.get_data()
    school = data.get("school", "Школа №1")
    
    users_data[user_id] = {
        "school": school,
        "city": city,
        "kp": 0,
        "st": 0,
        "level": 1,
        "taps": 0,
        "login_streak": 1,
        "last_login": datetime.now().isoformat(),
        "battle_wins": 0,
        "battle_losses": 0
    }
    
    await message.answer(
        f"✅ Отлично! Ты зачислен в {school}, г. {city}!\n\n"
        f"🎓 Начинай свое приключение! 🚀",
        reply_markup=get_main_keyboard(user_id)  # ← ВАЖНО!
    )
    await state.clear()

# ==================== ОБРАБОТЧИКИ КНОПОК ====================

@dp.callback_query(lambda c: c.data == "tap")
async def handle_tap(callback: types.CallbackQuery):
    """Обработчик тапа"""
    user_id = callback.from_user.id
    
    if user_id not in users_data:
        await callback.answer("❌ Сначала зарегистрируйся через /start", show_alert=True)
        return
    
    user = users_data[user_id]
    user["kp"] += 1
    user["taps"] += 1
    
    # Каждые 10 тапов даем мысль ученого
    if user["taps"] % 10 == 0:
        user["st"] += 1
        await callback.answer(f"🧠 +1 Мысль ученого! (Всего: {user['st']})")
    else:
        await callback.answer(f"📚 +1 Очко знаний! (Всего: {user['kp']})")
    
    # Проверяем уровень (каждые 100 очков)
    new_level = user["kp"] // 100 + 1
    if new_level > user.get("level", 1):
        user["level"] = new_level
        await callback.answer(f"🎉 Уровень повышен! Ты теперь {new_level} уровень!", show_alert=True)

@dp.callback_query(lambda c: c.data == "stats")
async def show_stats(callback: types.CallbackQuery):
    """Показывает статистику"""
    user_id = callback.from_user.id
    
    if user_id not in users_data:
        await callback.answer("❌ Сначала зарегистрируйся через /start", show_alert=True)
        return
    
    user = users_data[user_id]
    
    await callback.answer(
        f"📊 Твоя статистика:\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"📚 Очки знаний: {user['kp']}\n"
        f"🧠 Мысли ученого: {user['st']}\n"
        f"🏆 Уровень: {user['level']}\n"
        f"🖱️ Всего тапов: {user['taps']}\n"
        f"🏫 Школа: {user['school']}\n"
        f"🌆 Город: {user['city']}\n"
        f"🔥 Серия входов: {user.get('login_streak', 0)} дней\n"
        f"⚔️ Побед в баттлах: {user.get('battle_wins', 0)}\n"
        f"💔 Поражений: {user.get('battle_losses', 0)}",
        show_alert=True
    )

@dp.callback_query(lambda c: c.data == "change_school")
async def change_school(callback: types.CallbackQuery, state: FSMContext):
    """Смена школы"""
    user_id = callback.from_user.id
    
    if user_id not in users_data:
        await callback.answer("❌ Сначала зарегистрируйся через /start", show_alert=True)
        return
    
    await callback.message.edit_text(
        "🏫 Выбери свою школу:",
        reply_markup=get_school_keyboard()
    )
    await callback.answer()
    await state.set_state(RegisterStates.waiting_for_school)

@dp.callback_query(lambda c: c.data == "bonus")
async def get_bonus(callback: types.CallbackQuery):
    """Ежедневный бонус"""
    user_id = callback.from_user.id
    
    if user_id not in users_data:
        await callback.answer("❌ Сначала зарегистрируйся через /start", show_alert=True)
        return
    
    user = users_data[user_id]
    today = datetime.now().date().isoformat()
    last_bonus = user.get("last_bonus", "")
    
    if last_bonus == today:
        await callback.answer("❌ Ты уже получал бонус сегодня! Приходи завтра.", show_alert=True)
        return
    
    bonus = 50 + user.get("login_streak", 0) * 5
    user["kp"] += bonus
    user["last_bonus"] = today
    
    await callback.answer(
        f"🎉 +{bonus} Очков знаний!\n"
        f"🔥 Серия входов: {user.get('login_streak', 0)} дней",
        show_alert=True
    )

@dp.callback_query(lambda c: c.data == "roulette")
async def roulette(callback: types.CallbackQuery):
    """Рулетка"""
    import random
    user_id = callback.from_user.id
    
    if user_id not in users_data:
        await callback.answer("❌ Сначала зарегистрируйся через /start", show_alert=True)
        return
    
    user = users_data[user_id]
    
    if user.get("kp", 0) < 1000:
        await callback.answer("❌ Нужно 1000 очков знаний для рулетки!", show_alert=True)
        return
    
    user["kp"] -= 1000
    
    rewards = [
        (10, 30), (50, 25), (100, 20), (250, 15),
        (500, 7), (1000, 2), (2500, 0.5), (5000, 0.1)
    ]
    
    total_weight = sum(w for _, w in rewards)
    roll = random.random() * total_weight
    
    cumulative = 0
    reward = 10
    
    for value, weight in rewards:
        cumulative += weight
        if roll <= cumulative:
            reward = value
            break
    
    if random.random() < 0.000001:
        reward = "telegram_premium"
    
    if reward == "telegram_premium":
        user["kp"] += 10000
        await callback.answer(
            "🎉🎉🎉 ПОЗДРАВЛЯЮ!\n"
            "Ты выиграл Telegram Premium на 1 месяц!\n"
            "Сделай скриншот и напиши @admin!",
            show_alert=True
        )
    else:
        user["kp"] += reward
        emoji = "🎉" if reward >= 500 else "✨" if reward >= 100 else "🎯"
        await callback.answer(f"{emoji} Ты выиграл {reward} очков знаний!", show_alert=True)

@dp.callback_query(lambda c: c.data == "battle")
async def start_battle(callback: types.CallbackQuery):
    """Начать баттл"""
    user_id = callback.from_user.id
    
    if user_id not in users_data:
        await callback.answer("❌ Сначала зарегистрируйся через /start", show_alert=True)
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="😊 Новичок (легко)", callback_data="battle_easy")],
        [InlineKeyboardButton(text="😤 Хулиган (средне)", callback_data="battle_medium")],
        [InlineKeyboardButton(text="🧠 Отличник (сложно)", callback_data="battle_hard")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
    ])
    
    await callback.message.edit_text(
        "⚔️ Выбери уровень сложности:\n\n"
        "😊 Новичок - 3 тапа/сек\n"
        "😤 Хулиган - 5 тапов/сек\n"
        "🧠 Отличник - 8 тапов/сек",
        reply_markup=keyboard
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("battle_"))
async def battle_fight(callback: types.CallbackQuery):
    """Симуляция баттла"""
    import random
    user_id = callback.from_user.id
    level = callback.data.replace("battle_", "")
    
    if user_id not in users_data:
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    user = users_data[user_id]
    
    bot_settings = {
        "easy": {"name": "Новичок", "speed": 3, "reward": 90},
        "medium": {"name": "Хулиган", "speed": 5, "reward": 310},
        "hard": {"name": "Отличник", "speed": 8, "reward": 500}
    }
    
    settings = bot_settings.get(level, bot_settings["easy"])
    
    user_score = random.randint(50, 100)
    bot_score = settings["speed"] * random.randint(8, 12)
    user_score += random.randint(-10, 20)
    bot_score += random.randint(-5, 10)
    
    if user_score > bot_score:
        reward = settings["reward"]
        user["kp"] += reward
        user["battle_wins"] = user.get("battle_wins", 0) + 1
        
        await callback.message.edit_text(
            f"⚔️ РЕЗУЛЬТАТ БАТТЛА\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"Противник: {settings['name']}\n"
            f"Ты: {user_score} очков\n"
            f"Бот: {bot_score} очков\n\n"
            f"🎉 ПОБЕДА!\n"
            f"📚 +{reward} очков знаний!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⚔️ Еще баттл", callback_data="battle")],
                [InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_menu")]
            ])
        )
    else:
        user["battle_losses"] = user.get("battle_losses", 0) + 1
        user["kp"] += 10
        
        await callback.message.edit_text(
            f"⚔️ РЕЗУЛЬТАТ БАТТЛА\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"Противник: {settings['name']}\n"
            f"Ты: {user_score} очков\n"
            f"Бот: {bot_score} очков\n\n"
            f"💔 ПОРАЖЕНИЕ...\n"
            f"📚 +10 утешительных очков",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⚔️ Попробовать снова", callback_data="battle")],
                [InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_menu")]
            ])
        )
    
    await callback.answer()

@dp.callback_query(lambda c: c.data == "shop")
async def open_shop(callback: types.CallbackQuery):
    """Магазин"""
    user_id = callback.from_user.id
    
    if user_id not in users_data:
        await callback.answer("❌ Сначала зарегистрируйся через /start", show_alert=True)
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎒 Аватары", callback_data="shop_avatars")],
        [InlineKeyboardButton(text="🖼️ Фоны", callback_data="shop_backgrounds")],
        [InlineKeyboardButton(text="🎨 Цвет ника", callback_data="shop_colors")],
        [InlineKeyboardButton(text="💎 Подписка", callback_data="shop_subscription")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
    ])
    
    await callback.message.edit_text(
        "💎 ДОБРО ПОЖАЛОВАТЬ В МАГАЗИН!\n"
        "━━━━━━━━━━━━━━━━\n"
        "Здесь можно купить:\n"
        "🎒 Аватары - измени внешность\n"
        "🖼️ Фоны - укрась игру\n"
        "🎨 Цвет ника - выделись\n"
        "💎 Подписка - получи премиум",
        reply_markup=keyboard
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "shop_avatars")
async def shop_avatars(callback: types.CallbackQuery):
    """Магазин аватаров"""
    user_id = callback.from_user.id
    
    if user_id not in users_data:
        await callback.answer("❌ Сначала зарегистрируйся через /start", show_alert=True)
        return
    
    user = users_data[user_id]
    
    avatars = [
        {"id": "default", "name": "🧑‍🎓 Стандартный", "price": 0, "owned": True},
        {"id": "nerd", "name": "📚 Отличник", "price": 5000, "owned": user.get("kp", 0) >= 5000},
        {"id": "bully", "name": "😈 Хулиган", "price": 50000, "owned": user.get("kp", 0) >= 50000},
    ]
    
    buttons = []
    for avatar in avatars:
        status = "✅" if avatar["owned"] else f"💰 {avatar['price']}"
        buttons.append([InlineKeyboardButton(
            f"{avatar['name']} {status}",
            callback_data=f"buy_avatar_{avatar['id']}"
        )])
    
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="shop")])
    
    await callback.message.edit_text(
        "🎒 АВАТАРЫ\n"
        "━━━━━━━━━━━━━━━━\n"
        "Выбери своего школьника:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("buy_avatar_"))
async def buy_avatar(callback: types.CallbackQuery):
    """Покупка аватара"""
    user_id = callback.from_user.id
    avatar_id = callback.data.replace("buy_avatar_", "")
    
    if user_id not in users_data:
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    user = users_data[user_id]
    
    prices = {"nerd": 5000, "bully": 50000}
    price = prices.get(avatar_id, 0)
    
    if user.get("kp", 0) < price:
        await callback.answer(f"❌ Не хватает очков! Нужно {price} KP", show_alert=True)
        return
    
    user["kp"] -= price
    user["avatar"] = avatar_id
    
    await callback.answer("✅ Аватар куплен и активирован!", show_alert=True)
    await open_shop(callback)

@dp.callback_query(lambda c: c.data == "rating")
async def show_rating(callback: types.CallbackQuery):
    """Рейтинг игроков"""
    if not users_data:
        await callback.answer("❌ Пока нет игроков", show_alert=True)
        return
    
    sorted_users = sorted(
        users_data.items(),
        key=lambda x: x[1].get("kp", 0),
        reverse=True
    )[:10]
    
    rating_text = "📈 ТОП ИГРОКОВ\n━━━━━━━━━━━━━━━━\n"
    for i, (uid, data) in enumerate(sorted_users, 1):
        try:
            user = await bot.get_chat(uid)
            name = user.first_name or f"Игрок {uid}"
        except:
            name = f"Игрок {uid}"
        
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        rating_text += f"{medal} {name} - {data.get('kp', 0)} KP\n"
    
    await callback.answer(rating_text, show_alert=True)

@dp.callback_query(lambda c: c.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery):
    """Возврат в главное меню"""
    user_id = callback.from_user.id
    
    if user_id not in users_data:
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    user = users_data[user_id]
    
    await callback.message.edit_text(
        f"🎓 Привет, {callback.from_user.first_name}!\n"
        f"🏫 Школа: {user.get('school', 'Не выбрана')}\n"
        f"📚 Очки знаний: {user.get('kp', 0)}\n"
        f"🧠 Мысли ученого: {user.get('st', 0)}\n"
        f"🏆 Уровень: {user.get('level', 1)}\n\n"
        f"Выбери действие:",
        reply_markup=get_main_keyboard(user_id)
    )
    await callback.answer()

# ==================== ЗАПУСК ====================

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    print("🤖 Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
