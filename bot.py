import asyncio
import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
)
from aiohttp import web

BOT_TOKEN = os.getenv("BOT_TOKEN", "ВАШ_ТОКЕН_ОТ_BOTFATHER")
ADMIN_ID = int(os.getenv("ADMIN_ID", "ВАШ_TELEGRAM_ID"))
MINI_APP_URL = "https://dyadyakomol.github.io/mmm-store-app/"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def start_cmd(message: types.Message):
  kb = InlineKeyboardMarkup(
      inline_keyboard=[[
          InlineKeyboardButton(
              text="💎 Открыть M.M.M Store",
              web_app=WebAppInfo(url=MINI_APP_URL),
          )
      ]]
  )
  await message.answer(
      f"Здравствуйте, {message.from_user.first_name}!\n\n"
      "Добро пожаловать в **M.M.M Store** ✦\n"
      "Нажмите кнопку ниже, чтобы открыть каталог услуг.",
      reply_markup=kb,
      parse_mode="Markdown",
  )


@dp.message(F.web_app_data)
async def handle_webapp_data(message: types.Message):
  data = message.web_app_data.data
  user = message.from_user

  admin_text = (
      f"🚨 **НОВАЯ ЗАЯВКА ИЗ MINI APP!**\n\n"
      f"👤 Клиент: @{user.username or 'без никнейма'} (ID: `{user.id}`)\n"
      f"📦 Данные заказа:\n`{data}`"
  )
  if ADMIN_ID:
    try:
      await bot.send_message(
          chat_id=ADMIN_ID, text=admin_text, parse_mode="Markdown"
      )
    except Exception as e:
      print(f"Ошибка отправки админу: {e}")

  await message.answer(
      "✅ Ваша заявка успешно принята! Администратор свяжется с вами в"
      " течение пары минут."
  )


# Простой веб-сервер, чтобы Render держал процесс активным
async def handle_ping(request):
  return web.Response(text="M.M.M Store Bot is running 24/7!")


async def main():
  app = web.Application()
  app.router.add_get("/", handle_ping)
  runner = web.AppRunner(app)
  await runner.setup()
  port = int(os.getenv("PORT", 8080))
  site = web.TCPSite(runner, "0.0.0.0", port)
  await site.start()

  print(f"Бот и веб-сервер запущены на порту {port}")
  await bot.delete_webhook(drop_pending_updates=True)
  await dp.start_polling(bot)


if __name__ == "__main__":
  asyncio.run(main())
