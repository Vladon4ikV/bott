import asyncio, logging
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

# ---------- КЛАВИАТУРЫ ----------
def main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("🎮 Играть", web_app=WebAppInfo(url=WEB_APP_URL))],
        [InlineKeyboardButton("👆 Тап", callback_data="tap"),
         InlineKeyboardButton("📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton("🎁 Бонус", callback_data="bonus"),
         InlineKeyboardButton("⚔️ Баттл", callback_data="battle")],
        [InlineKeyboardButton("🎡 Рулетка", callback_data="roulette"),
         InlineKeyboardButton("💎 Магазин", callback_data="shop")],
        [InlineKeyboardButton("📈 Рейтинг", callback_data="rating")]
    ])

def school_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(f"🏫 Школа {i}", callback_data=f"sch_{i}") for i in range(1,5)],
        [InlineKeyboardButton("✏️ Вручную", callback_data="sch_manual")]
    ])

def city_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(c, callback_data=f"city_{c}") for c in ["Москва","СПб","Казань"]],
        [InlineKeyboardButton("✏️ Вручную", callback_data="city_manual")]
    ])

# ---------- /START ----------
@dp.message(Command("start"))
async def start(msg: types.Message, state: FSMContext):
    db = next(get_db())
    user = db.query(User).filter_by(telegram_id=msg.from_user.id).first()
    if not user:
        await msg.answer("Выбери школу:", reply_markup=school_kb())
        await state.set_state(Reg.school)
        return
    await msg.answer(f"Привет, {user.first_name}!\nKP: {user.kp}  ST: {user.st}", reply_markup=main_kb())

# ---------- РЕГИСТРАЦИЯ ----------
@dp.callback_query(Reg.school)
async def reg_school(call: types.CallbackQuery, state: FSMContext):
    if call.data == "sch_manual":
        await call.message.answer("Введи название школы")
        return
    await state.update_data(school=call.data.replace("sch_",""))
    await call.message.edit_text("Выбери город:", reply_markup=city_kb())
    await state.set_state(Reg.city)

@dp.callback_query(Reg.city)
async def reg_city(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    city = call.data.replace("city_","")
    db = next(get_db())
    user = User(
        telegram_id=call.from_user.id,
        username=call.from_user.username,
        first_name=call.from_user.first_name,
        school=data["school"],
        city=city
    )
    db.add(user)
    db.commit()
    await call.message.edit_text("✅ Готово!", reply_markup=main_kb())
    await state.clear()

# ---------- ОСНОВНОЙ ФУНКЦИОНАЛ ----------
@dp.callback_query(lambda c: c.data == "tap")
async def tap(call: types.CallbackQuery):
    db = next(get_db())
    u = db.query(User).filter_by(telegram_id=call.from_user.id).first()
    if not u: return await call.answer("Напиши /start")
    u.kp += 1
    u.taps += 1
    if u.taps % 10 == 0: u.st += 1
    if u.kp // 100 + 1 > u.level:
        u.level = u.kp // 100 + 1
    db.commit()
    await call.answer(f"KP: {u.kp}  ST: {u.st}")

@dp.callback_query(lambda c: c.data == "stats")
async def stats(call: types.CallbackQuery):
    db = next(get_db())
    u = db.query(User).filter_by(telegram_id=call.from_user.id).first()
    if not u: return
    await call.answer(
        f"KP: {u.kp}\nST: {u.st}\nLevel: {u.level}\nШкола: {u.school}\nГород: {u.city}",
        show_alert=True
    )

@dp.callback_query(lambda c: c.data == "bonus")
async def bonus(call: types.CallbackQuery):
    db = next(get_db())
    u = db.query(User).filter_by(telegram_id=call.from_user.id).first()
    now = datetime.utcnow().date()
    if u.last_login and u.last_login.date() == now:
        return await call.answer("Сегодня уже получал")
    u.last_login = datetime.utcnow()
    u.login_streak = u.login_streak + 1 if u.last_login and (now - u.last_login.date()).days == 1 else 1
    add = 50 + u.login_streak * 5
    u.kp += add
    db.commit()
    await call.answer(f"🎁 +{add} KP")

@dp.callback_query(lambda c: c.data == "roulette")
async def roulette(call: types.CallbackQuery):
    import random
    db = next(get_db())
    u = db.query(User).filter_by(telegram_id=call.from_user.id).first()
    if u.kp < 1000: return await call.answer("Нужно 1000 KP")
    u.kp -= 1000
    win = random.choices([10,50,150,300,500,1000,2500,5000], weights=[30,25,20,15,7,2,0.5,0.1])[0]
    u.kp += win
    db.commit()
    await call.answer(f"🎉 {win} KP", show_alert=True)

@dp.callback_query(lambda c: c.data == "battle")
async def battle_menu(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("😊 Лёгкий", callback_data="battle_easy"),
         InlineKeyboardButton("😤 Средний", callback_data="battle_medium"),
         InlineKeyboardButton("🧠 Сложный", callback_data="battle_hard")]
    ])
    await call.message.edit_text("Выбери сложность:", reply_markup=kb)

@dp.callback_query(lambda c: c.data.startswith("battle_"))
async def battle_fight(call: types.CallbackQuery):
    import random
    db = next(get_db())
    u = db.query(User).filter_by(telegram_id=call.from_user.id).first()
    lvl = call.data.replace("battle_","")
    rewards = {"easy":90, "medium":310, "hard":500}
    bot_score = {"easy":3, "medium":5, "hard":8}[lvl] * random.randint(8,13)
    user_score = random.randint(50,120)
    if user_score > bot_score:
        u.kp += rewards[lvl]
        u.battle_wins += 1
        res = f"🎉 Победа! +{rewards[lvl]} KP"
    else:
        u.kp += 10
        u.battle_losses += 1
        res = "💔 Поражение. +10 KP"
    db.commit()
    await call.message.edit_text(f"{res}\nТы: {user_score} | Бот: {bot_score}", reply_markup=main_kb())

# ---------- МАГАЗИН + ОПЛАТА ----------
@dp.callback_query(lambda c: c.data == "shop")
async def shop(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("1 задача (15₽)", callback_data="buy_task_1")],
        [InlineKeyboardButton("3 задачи (45₽)", callback_data="buy_task_3")],
        [InlineKeyboardButton("10 задач (150₽)", callback_data="buy_task_10")],
        [InlineKeyboardButton("1 день (75₽)", callback_data="buy_day")],
        [InlineKeyboardButton("1 неделя (249₽)", callback_data="buy_week")],
        [InlineKeyboardButton("1 месяц (349₽)", callback_data="buy_month")],
        [InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]
    ])
    await call.message.edit_text("💎 Магазин", reply_markup=kb)

@dp.callback_query(lambda c: c.data.startswith("buy_"))
async def buy(call: types.CallbackQuery):
    item_id = call.data.replace("buy_","")
    prices = {
        "task_1":15, "task_3":45, "task_10":150,
        "day":75, "week":249, "month":349
    }
    item_type = "tasks" if "task" in item_id else "subscription"
    amount = prices[item_id]
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
    await call.message.answer(f"💳 Оплати по ссылке:\n{payment['confirmation']['confirmation_url']}")

@dp.callback_query(lambda c: c.data == "rating")
async def rating(call: types.CallbackQuery):
    db = next(get_db())
    top = db.query(User).order_by(User.kp.desc()).limit(10).all()
    text = "🏆 ТОП\n" + "\n".join([f"{i+1}. {u.first_name} — {u.kp} KP" for i,u in enumerate(top)])
    await call.answer(text, show_alert=True)

@dp.callback_query(lambda c: c.data == "main_menu")
async def main_menu(call: types.CallbackQuery):
    await call.message.edit_text("Главное меню", reply_markup=main_kb())

# ---------- ЗАПУСК ----------
async def main():
    await bot.delete_webhook()
    print("✅ Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())