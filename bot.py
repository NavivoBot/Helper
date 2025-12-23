
# NAVIVO GOD LEVEL BOT
import asyncio, json, os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

BOT_TOKEN = "PASTE_YOUR_BOT_TOKEN_HERE"
bot = Bot(BOT_TOKEN)
dp = Dispatcher()

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

def load(name):
    path = f"{DATA_DIR}/{name}.json"
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save(name, data):
    with open(f"{DATA_DIR}/{name}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

users = load("users")
orders = load("orders")

SERVICES = {
    "anmeldung": {
        "price": 39,
        "steps": [
            {"id": "fullname", "fa": "نام کامل شما؟", "en": "Your full name?"},
            {"id": "address", "fa": "آدرس محل سکونت؟", "en": "Your address?"},
            {"id": "birth", "fa": "تاریخ تولد؟", "en": "Birth date?"},
            {"id": "arrival", "fa": "تاریخ ورود؟", "en": "Arrival date?"},
            {"id": "review", "fa": "بررسی نهایی", "en": "Final review"}
        ],
        "next": ["bank","sim"]
    },
    "bank": {
        "price": 49,
        "steps": [
            {"id": "city", "fa": "شهر محل زندگی؟", "en": "City?"},
            {"id": "bank", "fa": "بانک مورد نظر؟", "en": "Preferred bank?"},
            {"id": "review", "fa": "بررسی نهایی", "en": "Final review"}
        ],
        "next": ["sim"]
    },
    "sim": {
        "price": 19,
        "steps": [
            {"id": "provider", "fa": "اپراتور مدنظر؟", "en": "Provider?"},
            {"id": "review", "fa": "بررسی نهایی", "en": "Final review"}
        ],
        "next": []
    }
}

FREE_STEPS = 1

def get_user(uid):
    uid = str(uid)
    if uid not in users:
        users[uid] = {"lang":None,"service":None,"step":0,"answers":{},"paid":False}
        save("users", users)
    return users[uid]

def progress(user, service):
    total = len(SERVICES[service]["steps"])
    done = user["step"]
    pct = int((done/total)*100)
    bar = "█"*(pct//10)+"░"*(10-pct//10)
    return f"{bar} {pct}%"

@dp.message(Command("start"))
async def start(m: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇮🇷 فارسی", callback_data="lang_fa")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")]
    ])
    await m.answer("🌍 Welcome to Navivo\nSelect language:", reply_markup=kb)

@dp.callback_query(F.data.startswith("lang_"))
async def set_lang(c: CallbackQuery):
    user = get_user(c.from_user.id)
    user["lang"] = c.data.split("_")[1]
    save("users", users)
    await show_menu(c.message, user["lang"])

async def show_menu(msg, lang):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Anmeldung", callback_data="service_anmeldung")],
        [InlineKeyboardButton(text="🏦 Bank Account", callback_data="service_bank")],
        [InlineKeyboardButton(text="📱 SIM Card", callback_data="service_sim")]
    ])
    await msg.answer("📋 Main Menu" if lang=="en" else "📋 منوی اصلی", reply_markup=kb)

@dp.callback_query(F.data.startswith("service_"))
async def select_service(c: CallbackQuery):
    service = c.data.split("_")[1]
    user = get_user(c.from_user.id)
    user.update({"service":service,"step":0,"answers":{},"paid":False})
    save("users", users)
    await next_step(c.message, user)

async def next_step(msg, user):
    service = user["service"]
    lang = user["lang"]
    steps = SERVICES[service]["steps"]

    if user["step"] >= FREE_STEPS and not user["paid"]:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Pay & Continue", callback_data="pay")],
            [InlineKeyboardButton(text="💼 Do it for me", callback_data="delegate")]
        ])
        await msg.answer("🔒 Payment required" if lang=="en" else "🔒 نیاز به پرداخت", reply_markup=kb)
        return

    if user["step"] >= len(steps):
        await finish(msg, user)
        return

    q = steps[user["step"]][lang]
    await msg.answer(f"{progress(user,service)}\n\n{q}")

@dp.message()
async def collect(m: Message):
    user = get_user(m.from_user.id)
    if not user["service"]:
        return
    step_id = SERVICES[user["service"]]["steps"][user["step"]]["id"]
    user["answers"][step_id] = m.text
    user["step"] += 1
    save("users", users)
    await next_step(m, user)

@dp.callback_query(F.data=="pay")
async def pay(c: CallbackQuery):
    user = get_user(c.from_user.id)
    user["paid"] = True
    save("users", users)
    await c.message.answer("✅ Payment confirmed")
    await next_step(c.message, user)

@dp.callback_query(F.data=="delegate")
async def delegate(c: CallbackQuery):
    oid = str(len(orders)+1)
    orders[oid] = {
        "user":c.from_user.id,
        "service":get_user(c.from_user.id)["service"],
        "answers":get_user(c.from_user.id)["answers"],
        "status":"pending"
    }
    save("orders", orders)
    await c.message.answer("📨 Order received")

async def finish(msg, user):
    pdf = f"{DATA_DIR}/{user['service']}_{msg.from_user.id}.pdf"
    c = canvas.Canvas(pdf, pagesize=A4)
    y=800
    for k,v in user["answers"].items():
        c.drawString(50,y,f"{k}: {v}")
        y-=20
    c.save()
    await msg.answer_document(open(pdf,"rb"))
    user.update({"service":None,"step":0,"answers":{},"paid":False})
    save("users", users)
    await show_menu(msg, user["lang"])

async def main():
    await dp.start_polling(bot)

if __name__=="__main__":
    asyncio.run(main())
