import os
import asyncio
import sqlite3
from datetime import datetime
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
MINI_APP_URL = "https://dyadyakomol.github.io/mmm-store-app/"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

DB_FILE = "orders.sqlite3"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service TEXT,
            details TEXT,
            amount INTEGER DEFAULT 0,
            contact TEXT,
            status TEXT DEFAULT 'new',
            created_at TEXT,
            order_date TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 Открыть M.M.M Store", web_app=WebAppInfo(url=MINI_APP_URL))]
    ])
    await message.answer(
        f"Здравствуйте, {message.from_user.first_name}!\n\n"
        "Добро пожаловать в **M.M.M Store** ✦\n"
        "Нажмите кнопку ниже, чтобы открыть витрину.",
        reply_markup=kb,
        parse_mode="Markdown"
    )

def extract_amount(details_str):
    nums = "".join([c for c in details_str if c.isdigit()])
    return int(nums) if nums else 0

# 1. Прием заказа
async def handle_new_order(request):
    try:
        data = await request.json()
        service = data.get("service", "Товар / Услуга")
        details = data.get("details", "—")
        contact = data.get("contact", "Не указан")
        amount = extract_amount(details)
        now = datetime.now()
        created_at = now.strftime("%d.%m.%Y %H:%M")
        order_date = now.strftime("%Y-%m-%d")

        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO orders (service, details, amount, contact, status, created_at, order_date)
            VALUES (?, ?, ?, ?, 'new', ?, ?)
        """, (service, details, amount, contact, created_at, order_date))
        order_id = cur.lastrowid
        conn.commit()
        conn.close()

        if ADMIN_ID:
            msg = (
                f"🚨 **НОВЫЙ ЗАКАЗ #{order_id}**\n\n"
                f"📦 **Услуга:** {service}\n"
                f"💰 **Сумма:** {details}\n"
                f"👤 **Клиент:** {contact}\n"
                f"🕒 **Дата:** {created_at}"
            )
            try:
                await bot.send_message(chat_id=ADMIN_ID, text=msg, parse_mode="Markdown")
            except Exception as err:
                print(f"Ошибка отправки админу: {err}")

        return web.json_response({"status": "ok", "order_id": order_id}, headers={"Access-Control-Allow-Origin": "*"})
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=400, headers={"Access-Control-Allow-Origin": "*"})

# 2. Получение списка всех заказов
async def handle_get_orders(request):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT id, service, details, amount, contact, status, created_at, order_date FROM orders ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()

    orders = []
    for r in rows:
        orders.append({
            "id": r[0],
            "service": r[1],
            "details": r[2],
            "amount": r[3],
            "contact": r[4],
            "status": r[5],
            "time": r[6],
            "date": r[7]
        })
    return web.json_response(orders, headers={"Access-Control-Allow-Origin": "*"})

# 3. Смена статуса заказа
async def handle_update_status(request):
    try:
        data = await request.json()
        order_id = data.get("id")
        new_status = data.get("status")

        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
        conn.commit()
        conn.close()
        return web.json_response({"status": "ok"}, headers={"Access-Control-Allow-Origin": "*"})
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=400, headers={"Access-Control-Allow-Origin": "*"})

async def handle_cors(request):
    return web.Response(headers={
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type"
    })

async def main():
    app = web.Application()
    app.router.add_get("/", lambda req: web.Response(text="M.M.M Store Backend Live!"))
    app.router.add_post("/api/order", handle_new_order)
    app.router.add_get("/api/orders", handle_get_orders)
    app.router.add_post("/api/order/status", handle_update_status)
    
    app.router.add_route("OPTIONS", "/api/order", handle_cors)
    app.router.add_route("OPTIONS", "/api/orders", handle_cors)
    app.router.add_route("OPTIONS", "/api/order/status", handle_cors)

    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    print(f"Сервер слушает порт {port}")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
