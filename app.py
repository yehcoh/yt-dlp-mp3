from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, JSONResponse
import yt_dlp
import os
import time
from pathlib import Path

app = FastAPI()

# תיקייה לשמירת MP3 זמניים
DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

# כמה שניות קבצים ישמרו (1 שעה)
MAX_AGE = 3600  

# מחיקת קבצים ישנים
def cleanup_old_files():
    now = time.time()
    for file in DOWNLOAD_DIR.iterdir():
        if file.is_file() and now - file.stat().st_mtime > MAX_AGE:
            file.unlink()

@app.get("/download")
def download_mp3(url: str = Query(..., description="YouTube video URL")):
    cleanup_old_files()  # מנקה קודם כל קבצים ישנים

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': str(DOWNLOAD_DIR / '%(title)s.%(ext)s'),
        'cookies': 'cookies.txt',  # כאן העוגיות שלך
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = DOWNLOAD_DIR / f"{info['title']}.mp3"
            if not filename.exists():
                return JSONResponse({"error": "MP3 not found after download"}, status_code=500)
            
            # מחזיר URL לשרת שלך (Render) שמוביל ישירות לקובץ
            file_url = f"/stream/{filename.name}"
            return {"title": info['title'], "url": file_url}

    except yt_dlp.utils.DownloadError as e:
        return JSONResponse({"error": str(e)}, status_code=400)

@app.get("/stream/{filename}")
def stream_file(filename: str):
    file_path = DOWNLOAD_DIR / filename
    if file_path.exists():
        return FileResponse(file_path, media_type="audio/mpeg", filename=filename)
    else:
        return JSONResponse({"error": "File not found"}, status_code=404)
