import os
import subprocess

def start_buffer(court_id="court_1", rtsp_url="rtsp://192.168.0.1:554/live"):
    # Створюємо папаку buffer на рівень вище у головній папці проєкту, якщо її ще немає
    buffer_dir = "../buffer"
    os.makedirs(buffer_dir, exist_ok=True)
    
    playlist_path = os.path.join(buffer_dir, f"{court_id}.m3u8")
    segment_path = os.path.join(buffer_dir, f"{court_id}_%03d.ts")

    # FFmpeg команда для постійного кільцевого буфера (режим live HLS)
    # Зберігає останні хвилини у вигляді сегментів по 5 секунд (сумарно близько 1 хвилини)
    cmd = [
        r"D:\ffmpeg\bin\ffmpeg.exe",
        "-rtsp_transport", "tcp",
        "-i", rtsp_url,
        "-c", "copy",
        "-f", "hls",
        "-hls_time", "5",          # тривалість одного сегмента (5 секунд)
        "-hls_list_size", "24",     # 24 сегменти = рівно 2 хвилини буфера!
        "-hls_flags", "delete_segments+append_list",
        playlist_path
    ]

    print(f"Підключення до трансляції для {court_id} за адресою {rtsp_url}...")
    subprocess.run(cmd)

if __name__ == "__main__":
    # Запускаємо буферизацію для корту 1 з урахуванням IP-адреси роутера / телефону
    start_buffer("court_1", rtsp_url="rtsp://192.168.0.1:554/live")