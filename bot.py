import asyncio
import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from config import BOT_TOKEN, WEB_APP_URL
from database import get_db, User, Purchase
from yookassa_handler import yookassa

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)

class Reg(StatesGroup):
    school = State()
    city = State()

# ==================== КЛАВИАТУРЫ ====================

def main_kb():
    """Главное меню"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Играть", web_app=WebAppInfo(url=WEB_APP_URL))],
        [
            InlineKeyboardButton(text="👆 Тап", callback_data="tap"),
            InlineKeyboardButton(text="📊 Статистика", callback_data="stats")
        ],
        [
            InlineKeyboardButton(text="🎁 Бонус", callback_data="bonus"),
            InlineKeyboardButton(text="⚔️ Баттл", callback_data="battle")
        ],
        [
            InlineKeyboardButton(text="🎡 Рулетка", callback_data="roulette"),
            InlineKeyboardButton(text="💎 Магазин", callback_data="shop")
        ],
        [InlineKeyboardButton(text="📈 Рейтинг", callback_data="rating")]
    ])

def school_kb():
    """Выбор школы"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🏫 Школа 1", callback_data="sch_1"),
            InlineKeyboardButton(text="🏫 Школа 2", callback_data="sch_2")
        ],
        [
            InlineKeyboardButton(text="🏫 Школа 3", callback_data="sch_3"),
            InlineKeyboardButton(text="🏫 Школа 4", callback_data="sch_4")
        ],
        [InlineKeyboardButton(text="✏️ Ввести вручную", callback_data="sch_manual")]
    ])

def city_kb():
    """Выбор города"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🌆 Москва", callback_data="city_Москва"),
            InlineKeyboardButton(text="🌆 СПб", callback_data="city_СПб")
        ],
        [
            InlineKeyboardButton(text="🌆 Казань", callback_data="city_Казань"),
            InlineKeyboardButton(text="🌆 Новосибирск", callback_data="city_Новосибирск")
        ],
        [InlineKeyboardButton(text="✏️ Ввести вручную", callback_data="city_manual")]
    ])

# ==================== /START ====================

@dp.message(Command("start"))
async def start(msg: types.Message, state: FSMContext):
    db = next(get_db())
    user = db.query(User).filter_by(telegram_id=msg.from_user.id).first()
    
    if not user:
        await msg.answer("🎓 Добро пожаловать!\n\nВыбери свою школу:", reply_markup=school_kb())
        await state.set_state(Reg.school)
        return
    
    await msg.answer(
        f"🎓 Привет, {user.first_name}!\n"
        f"📚 KP: {user.kp}  🧠 ST: {user.st}\n"
        f"🏆 Уровень: {user.level}\n"
        f"🏫 {user.school} • {user.city}",
        reply_markup=main_kb()
    )

# ==================== РЕГИСТРАЦИЯ ====================

@dp.callback_query(Reg.school)
async def reg_school(call: types.CallbackQuery, state: FSMContext):
    if call.data == "sch_manual":
        await call.message.answer("✏️ Введи название школы:")
        await call.answer()
        return
    
    school = call.data.replace("sch_", "")
    await state.update_data(school=f"Школа {school}")
    
    await call.message.edit_text("🌆 Теперь выбери свой город:", reply_markup=city_kb())
    await call.answer()
    await state.set_state(Reg.city)

@dp.message(Reg.school)
async def reg_school_manual(msg: types.Message, state: FSMContext):
    await state.update_data(school=msg.text.strip())
    await msg.answer("🌆 Теперь выбери свой город:", reply_markup=city_kb())
    await state.set_state(Reg.city)

@dp.callback_query(Reg.city)
async def reg_city(call: types.CallbackQuery, state: FSMContext):
    if call.data == "city_manual":
        await call.message.answer("✏️ Введи название города:")
        await call.answer()
        return
    
    city = call.data.replace("city_", "")
    data = await state.get_data()
    school = data.get("school", "Школа 1")
    
    db = next(get_db())
    user = User(
        telegram_id=call.from_user.id,
        username=call.from_user.username,
        first_name=call.from_user.first_name,
        school=school,
        city=city
    )
    db.add(user)
    db.commit()
    
    await call.message.edit_text(
        f"✅ Отлично! Ты в {school}, г. {city}!\n\n"
        f"🎓 Начинай зарабатывать очки!",
        reply_markup=main_kb()
    )
    await call.answer()
    await state.clear()

@dp.message(Reg.city)
async def reg_city_manual(msg: types.Message, state: FSMContext):
    city = msg.text.strip()
    data = await state.get_data()
    school = data.get("school", "Школа 1")
    
    db = next(get_db())
    user = User(
        telegram_id=msg.from_user.id,
        username=msg.from_user.username,
        first_name=msg.from_user.first_name,
        school=school,
        city=city
    )
    db.add(user)
    db.commit()
    
    await msg.answer(
        f"✅ Отлично! Ты в {school}, г. {city}!\n\n"
        f"🎓 Начинай зарабатывать очки!",
        reply_markup=main_kb()
    )
    await state.clear()

# ==================== ОСНОВНЫЕ КНОПКИ ====================

@dp.callback_query(lambda c: c.data == "tap")
async def tap(call: types.CallbackQuery):
    db = next(get_db())
    user = db.query(User).filter_by(telegram_id=call.from_user.id).first()
    if not user:
        await call.answer("❌ Напиши /start")
        return
    
    user.kp += 1
    user.taps += 1
    
    if user.taps % 10 == 0:
        user.st += 1
        await call.answer(f"🧠 +1 ST! Всего: {user.st}")
    
    new_level = user.kp // 100 + 1
    if new_level > user.level:
        user.level = new_level
        await call.answer(f"🎉 УРОВЕНЬ {new_level}!", show_alert=True)
    
    db.commit()
    await call.answer(f"📚 +1 KP (Всего: {user.kp})")

@dp.callback_query(lambda c: c.data == "stats")
async def stats(call: types.CallbackQuery):
    db = next(get_db())
    user = db.query(User).filter_by(telegram_id=call.from_user.id).first()
    if not user:
        await call.answer("❌ Напиши /start")
        return
    
    await call.answer(
        f"📊 ТВОЯ СТАТИСТИКА\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"📚 KP: {user.kp}\n"
        f"🧠 ST: {user.st}\n"
        f"🏆 Уровень: {user.level}\n"
        f"👆 Тапов: {user.taps}\n"
        f"🏫 {user.school} • {user.city}\n"
        f"🔥 Серия: {user.login_streak} дней\n"
        f"⚔️ Побед: {user.battle_wins}\n"
        f"💔 Поражений: {user.battle_losses}",
        show_alert=True
    )

@dp.callback_query(lambda c: c.data == "bonus")
async def bonus(call: types.CallbackQuery):
    db = next(get_db())
    user = db.query(User).filter_by(telegram_id=call.from_user.id).first()
    if not user:
        await call.answer("❌ Напиши /start")
        return
    
    today = datetime.now().date().isoformat()
    last_bonus = getattr(user, "last_bonus", "")
    
    if last_bonus == today:
        await call.answer("❌ Бонус уже получен сегодня!", show_alert=True)
        return
    
    bonus_amount = 50 + user.login_streak * 5
    user.kp += bonus_amount
    user.last_bonus = today
    user.login_streak += 1
    
    db.commit()
    await call.answer(f"🎁 +{bonus_amount} KP!\n🔥 Серия: {user.login_streak} дней", show_alert=True)

@dp.callback_query(lambda c: c.data == "roulette")
async def roulette(call: types.CallbackQuery):
    import random
    db = next(get_db())
    user = db.query(User).filter_by(telegram_id=call.from_user.id).first()
    if not user:
        await call.answer("❌ Напиши /start")
        return
    
    if user.kp < 1000:
        await call.answer("❌ Нужно 1000 KP!", show_alert=True)
        return
    
    user.kp -= 1000
    
    rewards = [10, 50, 150, 300, 500, 1000, 2500, 5000]
    weights = [30, 25, 20, 15, 7, 2, 0.5, 0.1]
    win = random.choices(rewards, weights=weights)[0]
    
    if random.random() < 0.000001:
        user.kp += 10000
        db.commit()
        await call.answer("🎉🎉🎉 PREMIUM! Сделай скриншот и напиши админу!", show_alert=True)
        return
    
    user.kp += win
    db.commit()
    await call.answer(f"🎡 Выиграл: {win} KP!", show_alert=True)

@dp.callback_query(lambda c: c.data == "battle")
async def battle_menu(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="😊 Лёгкий", callback_data="battle_easy"),
            InlineKeyboardButton(text="😤 Средний", callback_data="battle_medium")
        ],
        [
            InlineKeyboardButton(text="🧠 Сложный", callback_data="battle_hard"),
            InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")
        ]
    ])
    await call.message.edit_text("⚔️ Выбери сложность:", reply_markup=kb)
    await call.answer()

@dp.callback_query(lambda c: c.data.startswith("battle_"))
async def battle_fight(call: types.CallbackQuery):
    import random
    db = next(get_db())
    user = db.query(User).filter_by(telegram_id=call.from_user.id).first()
    if not user:
        await call.answer("❌ Ошибка")
        return
    
    level = call.data.replace("battle_", "")
    settings = {
        "easy": {"name": "Новичок", "reward": 90, "bot_speed": 3},
        "medium": {"name": "Хулиган", "reward": 310, "bot_speed": 5},
        "hard": {"name": "Отличник", "reward": 500, "bot_speed": 8}
    }
    s = settings.get(level, settings["easy"])
    
    user_score = random.randint(50, 120)
    bot_score = s["bot_speed"] * random.randint(8, 13)
    
    if user_score > bot_score:
        user.kp += s["reward"]
        user.battle_wins += 1
        result = f"🎉 ПОБЕДА! +{s['reward']} KP"
    else:
        user.kp += 10
        user.battle_losses += 1
        result = f"💔 ПОРАЖЕНИЕ... +10 KP"
    
    db.commit()
    
    await call.message.edit_text(
        f"{result}\n\n"
        f"Ты: {user_score} | Бот: {bot_score}\n"
        f"Противник: {s['name']}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⚔️ Ещё", callback_data="battle")],
            [InlineKeyboardButton(text="🔙 Меню", callback_data="main_menu")]
        ])
    )
    await call.answer()

# ==================== МАГАЗИН И ОПЛАТА ====================

@dp.callback_query(lambda c: c.data == "shop")
async def shop(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 1 задача (15₽)", callback_data="buy_task_1")],
        [InlineKeyboardButton(text="📝 3 задачи (45₽)", callback_data="buy_task_3")],
        [InlineKeyboardButton(text="📝 10 задач (150₽)", callback_data="buy_task_10")],
        [InlineKeyboardButton(text="📅 1 день (75₽)", callback_data="buy_day")],
        [InlineKeyboardButton(text="📅 1 неделя (249₽)", callback_data="buy_week")],
        [InlineKeyboardButton(text="📅 1 месяц (349₽)", callback_data="buy_month")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
    ])
    await call.message.edit_text("💎 МАГАЗИН\n\nВыбери товар:", reply_markup=kb)
    await call.answer()

@dp.callback_query(lambda c: c.data.startswith("buy_"))
async def buy(call: types.CallbackQuery):
    item_id = call.data.replace("buy_", "")
    prices = {
        "task_1": 15, "task_3": 45, "task_10": 150,
        "day": 75, "week": 249, "month": 349
    }
    item_type = "tasks" if "task" in item_id else "subscription"
    amount = prices.get(item_id, 0)
    
    db = next(get_db())
    payment = yookassa.create_payment(
        user_id=call.from_user.id,
        amount=amount,
        description=f"Покупка {item_id}",
        metadata={"user_id": call.from_user.id, "item_type": item_type, "item_id": item_id}
    )
    
    p = Purchase(
        user_id=call.from_user.id,
        item_type=item_type,
        item_id=item_id,
        amount=amount,
        payment_id=payment["id"]
    )
    db.add(p)
    db.commit()
    
    await call.message.answer(
        f"💳 Оплати по ссылке:\n{payment['confirmation']['confirmation_url']}\n\n"
        f"После оплаты нажми /start для обновления"
    )
    await call.answer()

@dp.callback_query(lambda c: c.data == "rating")
async def rating(call: types.CallbackQuery):
    db = next(get_db())
    top = db.query(User).order_by(User.kp.desc()).limit(10).all()
    
    if not top:
        await call.answer("📊 Пока нет игроков", show_alert=True)
        return
    
    text = "🏆 ТОП 10\n━━━━━━━━━━━━\n"
    for i, u in enumerate(top, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        text += f"{medal} {u.first_name} — {u.kp} KP\n"
    
    await call.answer(text, show_alert=True)

@dp.callback_query(lambda c: c.data == "main_menu")
async def main_menu(call: types.CallbackQuery):
    db = next(get_db())
    user = db.query(User).filter_by(telegram_id=call.from_user.id).first()
    if not user:
        await call.answer("❌ Ошибка")
        return
    
    await call.message.edit_text(
        f"🎓 Привет, {user.first_name}!\n"
        f"📚 KP: {user.kp}  🧠 ST: {user.st}\n"
        f"🏆 Уровень: {user.level}\n"
        f"🏫 {user.school} • {user.city}",
        reply_markup=main_kb()
    )
    await call.answer()

# ==================== ЗАПУСК ====================

async def main():
    await bot.delete_webhook()
    print("✅ Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
