import subprocess
import requests
import json

TOKEN = "8781850648:AAFzH9FMpeuRJGFdSRFPVL1nVH2qBnpfONw"

def send_video_to_user(chat_id, video_path):
    url = f"https://api.telegram.org/bot{TOKEN}/sendVideo"
    with open(video_path, 'rb') as video_file:
        files = {'video': video_file}
        data = {'chat_id': chat_id, 'caption': 'Ось ваш хайлайт з гри! 🔥🎾'}
        response = requests.post(url, data=data, files=files)
        print("Результат відправки в Telegram:", response.json())

def save_and_send(court_id="court_1", target_chat_id=None):
    output_video = f"../final_{court_id}.mp4"
    
    # 1. Зшиваємо відео з буфера через FFmpeg
    cmd = f"ffmpeg -f concat -safe 0 -i ../buffer/{court_id}.m3u8 -c copy {output_video}"
    subprocess.run(cmd.split())
    print(f"Відео для {court_id} збережено!")

    # 2. Якщо знаємо chat_id користувача — відправляємо йому в Telegram
    if target_chat_id:
        send_video_to_user(target_chat_id, output_video)

if __name__ == "__main__":
    # Тестовий запуск для court_1 (тут пізніше підставимо реальний chat_id з бота)
    save_and_send("court_1")