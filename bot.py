import os
import asyncio
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

# База данных заказов в памяти сервера
ORDERS_DB = []

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 Открыть M.M.M Store", web_app=WebAppInfo(url=MINI_APP_URL))]
    ])
    await message.answer(
        f"Здравствуйте, {message.from_user.first_name}!\n\n"
        "Добро пожаловать в **M.M.M Store** ✦\n"
        "Нажмите кнопку ниже, чтобы открыть каталог услуг.",
        reply_markup=kb,
        parse_mode="Markdown"
    )

# 1. Прием заказа от приложения
async def handle_new_order(request):
    try:
        data = await request.json()
        item = {
            "id": len(ORDERS_DB) + 1,
            "service": data.get("service", "Товар / Услуга"),
            "details": data.get("details", "—"),
            "contact": data.get("contact", "Не указан"),
            "time": datetime.now().strftime("%d.%m %H:%M")
        }
        ORDERS_DB.append(item)

        # Моментальное уведомление вам в личку
        if ADMIN_ID:
            msg = (
                f"🚨 **НОВЫЙ ЗАКАЗ В M.M.M STORE!**\n\n"
                f"📦 **Услуга:** {item['service']}\n"
                f"💰 **Детали:** {item['details']}\n"
                f"👤 **Клиент:** {item['contact']}\n"
                f"🕒 **Время:** {item['time']}"
            )
            try:
                await bot.send_message(chat_id=ADMIN_ID, text=msg, parse_mode="Markdown")
            except Exception as err:
                print(f"Ошибка отправки админу: {err}")

        return web.json_response({"status": "ok"}, headers={"Access-Control-Allow-Origin": "*"})
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=400, headers={"Access-Control-Allow-Origin": "*"})

# 2. Передача заказов в админ-панель
async def handle_get_orders(request):
    return web.json_response(ORDERS_DB, headers={
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type"
    })

# Настройка CORS
async def handle_cors_options(request):
    return web.Response(headers={
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type"
    })

async def main():
    app = web.Application()
    app.router.add_get("/", lambda req: web.Response(text="M.M.M Backend Active!"))
    app.router.add_post("/api/order", handle_new_order)
    app.router.add_get("/api/orders", handle_get_orders)
    app.router.add_route("OPTIONS", "/api/order", handle_cors_options)
    app.router.add_route("OPTIONS", "/api/orders", handle_cors_options)

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
