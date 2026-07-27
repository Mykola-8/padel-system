import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder

TOKEN = "8781850648:AAFzH9FMpeuRJGFdSRFPVL1nVH2qBnpfONw"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# База активних користувачів та їх кортів: {chat_id: court_id}
active_users = {}

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Отримуємо корт із посилання (наприклад, /start court_1)
    args = message.text.split(maxsplit=1)
    court_id = args[1] if len(args) > 1 else "court_1"
    
    active_users[message.chat.id] = court_id

    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="📱 Підтвердити номер телефону", request_contact=True))
    
    await message.answer(
        f"Вітаємо у Padel Clip! 🎾\nВи на корті: <b>{court_id}</b>\n\n"
        "Натисніть кнопку нижче, щоб підтвердити номер:",
        reply_markup=builder.as_markup(resize_keyboard=True),
        parse_mode="HTML"
    )

@dp.message(lambda message: message.contact is not None)
async def handle_contact(message: types.Message):
    chat_id = message.chat.id
    phone = message.contact.phone_number
    court = active_users.get(chat_id, "court_1")
    
    # Реєструємо користувача на нашому локальному FastAPI сервері (щоб сервер знав його chat_id)
    import requests
    try:
        requests.post("http://127.0.0.1:8000/register-user", json={"court_id": court, "chat_id": chat_id})
    except Exception as e:
        print("Помилка реєстрації на сервері:", e)

    # Створюємо клавіатуру із головною кнопкою запису хайлайту
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="🎥 Зберегти хайлайт"))
    
    await message.answer(
        f"Дякуємо! Ваш номер {phone} зареєстровано. ✅\n\n"
        "Тепер під час гри просто натискайте кнопку нижче, і відео з останніх секунд автоматично надішлеться сюди!",
        reply_markup=builder.as_markup(resize_keyboard=True)
    )

@dp.message(lambda message: message.text == "🎥 Зберегти хайлайт")
async def handle_clip_request(message: types.Message):
    chat_id = message.chat.id
    court = active_users.get(chat_id, "court_1")
    
    await message.answer("⏳ Обробляємо відео з буфера, зачекайте кілька секунд...")

    # Звертаємося до нашого FastAPI сервера, який запустить FFmpeg і надішле відео
    import requests
    try:
        response = requests.get(f"http://127.0.0.1:8000/trigger/{court}")
        data = response.json()
        if not data.get("success"):
            await message.answer(f"⚠️ Не вдалося створити відео: {data.get('error', 'Спробуйте ще раз')}")
    except Exception as e:
        await message.answer("❌ Помилка зв'язку з сервером обробки відео.")

async def main():
    logging.basicConfig(level=logging.INFO)
    print("Telegram-бот запущено і готовий до роботи...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())