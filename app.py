from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, JSONResponse
import yt_dlp
import os
import time
from pathlib import Path

app = FastAPI()

# תיקייה להורדות
DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)
MAX_AGE = 3600  

def setup_auth():
    """יוצר קובץ עוגיות זמני ממשתנה הסביבה של Render"""
    cookies_content = os.getenv("YT_COOKIES_DATA")
    if cookies_content:
        cookie_file = Path("cookies.txt")
        cookie_file.write_text(cookies_content, encoding="utf-8")
        return str(cookie_file)
    return None

def cleanup_old_files():
    now = time.time()
    for file in DOWNLOAD_DIR.iterdir():
        if file.is_file() and now - file.stat().st_mtime > MAX_AGE:
            file.unlink()

@app.get("/download")
def download_mp3(url: str = Query(..., description="YouTube video URL")):
    cleanup_old_files()
    cookie_path = setup_auth()

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': str(DOWNLOAD_DIR / '%(title)s.%(ext)s'),
        'cookiefile': cookie_path, # שימוש בעוגיות שהכנו
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True,
        # הוספת User-Agent כדי להיראות כמו דפדפן אמיתי
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            # איתור הקובץ הסופי (מטפל בתווים מיוחדים ש-yt-dlp מנקה)
            actual_file = Path(ydl.prepare_filename(info)).with_suffix('.mp3')
            
            if not actual_file.exists():
                return JSONResponse({"error": "File generation failed"}, status_code=500)
            
            return {
                "title": info.get('title'),
                "url": f"/stream/{actual_file.name}"
            }

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)

@app.get("/stream/{filename}")
def stream_file(filename: str):
    file_path = DOWNLOAD_DIR / filename
    if file_path.exists():
        return FileResponse(file_path, media_type="audio/mpeg", filename=filename)
    return JSONResponse({"error": "File not found"}, status_code=404)
