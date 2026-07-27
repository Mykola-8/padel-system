from fastapi import FastAPI
import subprocess
import requests
import os
import threading
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder

app = FastAPI()

FFMPEG_PATH = "ffmpeg"  # У хмарі Linux ffmpeg зазвичай вже встановлений глобально у систему!
TELEGRAM_TOKEN = "8781850648:AAFzH9FMpeuRJGFdSRFPVL1nVH2qBnpfONw"

court_users = {}

@app.get("/")
def home():
    return {"status": "Padel Cloud Clip Server is running!"}

@app.get("/trigger/{court_id}")
def trigger_highlight(court_id: str):
    output_video = f"final_{court_id}.mp4"
    playlist_path = f"buffer/{court_id}.m3u8"
    
    if not os.path.exists(playlist_path):
        return {"success": False, "error": f"Буфер для {court_id} ще не створено або камера не пише потоки у хмару!"}

    cmd = [
        FFMPEG_PATH, 
        "-f", "concat", 
        "-safe", "0", 
        "-i", playlist_path, 
        "-c", "copy", 
        output_video
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        return {"success": False, "error": f"FFmpeg error: {result.stderr}"}

    target_chat_id = court_users.get(court_id)
    
    if target_chat_id:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo"
        with open(output_video, 'rb') as video_file:
            files = {'video': video_file}
            data = {'chat_id': target_chat_id, 'caption': 'Ось ваш хайлайт з гри! 🔥🎾'}
            requests.post(url, data=data, files=files)
        return {"success": True, "message": "Відео успішно відправлено!"}
    
    return {"success": True, "message": "Відео зшито, але користувача не знайдено."}

@app.post("/register-user")
def register_user(data: dict):
    court_id = data.get("court_id", "court_1")
    chat_id = data.get("chat_id")
    court_users[court_id] = chat_id
    return {"status": "registered"}


# --- ЗАПУСК TELEGRAM-БОТА У ФОНОВОМУ ПОТОЦІ ---
async def start_telegram_bot():
    bot = Bot(token=TELEGRAM_TOKEN)
    dp = Dispatcher()
    active_users = {}

    @dp.message(Command("start"))
    async def cmd_start(message: types.Message):
        args = message.text.split(maxsplit=1)
        court_id = args[1] if len(args) > 1 else "court_1"
        active_users[message.chat.id] = court_id

        builder = ReplyKeyboardBuilder()
        builder.add(types.KeyboardButton(text="📱 Підтвердити номер телефону", request_contact=True))
        
        await message.answer(
            f"Вітаємо у Padel Clip (Cloud)! 🎾\nВи на корті: <b>{court_id}</b>\n\n"
            "Натисніть кнопку нижче для авторизації:",
            reply_markup=builder.as_markup(resize_keyboard=True),
            parse_mode="HTML"
        )

    @dp.message(lambda message: message.contact is not None)
    async def handle_contact(message: types.Message):
        chat_id = message.chat.id
        phone = message.contact.phone_number
        court = active_users.get(chat_id, "court_1")
        
        try:
            requests.post("http://127.0.0.1:8000/register-user", json={"court_id": court, "chat_id": chat_id})
        except Exception:
            court_users[court] = chat_id # Реєструємо локально в пам'яті якщо шлях не пройшов

        builder = ReplyKeyboardBuilder()
        builder.add(types.KeyboardButton(text="🎥 Зберегти хайлайт"))
        
        await message.answer(
            f"Номер {phone} успішно зареєстровано! ✅\nТепер натискайте кнопку нижче під час гри:",
            reply_markup=builder.as_markup(resize_keyboard=True)
        )

    @dp.message(lambda message: message.text == "🎥 Зберегти хайлайт")
    async def handle_clip_request(message: types.Message):
        chat_id = message.chat.id
        court = active_users.get(chat_id, "court_1")
        
        await message.answer("⏳ Обробляємо відео з буфера...")
        try:
            # Звертаємось до нашого ж хмарного сервера
            response = requests.get(f"http://127.0.0.1:8000/trigger/{court}")
            data = response.json()
            if not data.get("success"):
                await message.answer(f"⚠️ {data.get('error', 'Спробуйте ще раз')}")
        except Exception:
            await message.answer("❌ Помилка зв'язку з буфером.")

    print("Фоновий Telegram бот запущено...")
    await dp.start_polling(bot)

def run_bot_in_background():
    asyncio.run(start_telegram_bot())

@app.on_event("startup")
def startup_event():
    # Запускаємо бота в окремому фоновому потоці при старті FastAPI
    t = threading.Thread(target=run_bot_in_background, daemon=True)
    t.start()