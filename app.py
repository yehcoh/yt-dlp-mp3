# main.py
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp
import os
import time
from pathlib import Path

app = FastAPI()

# CORS - לאפשר גישה מכל מקור
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ספריית הורדה זמנית
DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

# פונקציה לניקוי קבצים ישנים
def cleanup_old_files(max_age_seconds=3600):
    now = time.time()
    for f in DOWNLOAD_DIR.iterdir():
        if f.is_file() and (now - f.stat().st_mtime) > max_age_seconds:
            f.unlink()

@app.get("/download")
def download_mp3(url: str = Query(..., description="כתובת יוטיוב להורדה")):
    cleanup_old_files()  # ניקוי קבצים ישנים

    if not url.startswith("http"):
        raise HTTPException(status_code=400, detail="כתובת לא חוקית")

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': str(DOWNLOAD_DIR / '%(id)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            filename = DOWNLOAD_DIR / f"{info_dict['id']}.mp3"
            if not filename.exists():
                raise HTTPException(status_code=500, detail="MP3 לא נוצר")
            # מחזיר URL ישיר
            return {
                "status": "ok",
                "title": info_dict.get("title"),
                "download_url": f"/downloads/{filename.name}"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
