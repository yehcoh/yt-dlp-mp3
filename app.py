import os
from fastapi import FastAPI, HTTPException
from yt_dlp import YoutubeDL
import subprocess

app = FastAPI()

# פונקציה לבדוק ולעדכן yt-dlp אם צריך
def ensure_yt_dlp_latest():
    try:
        version = subprocess.check_output(["yt-dlp", "--version"]).decode().strip()
        # אפשר להשוות עם גרסה באתר אם רוצים, פה רק הדגמה
        print(f"Current yt-dlp version: {version}")
        subprocess.run(["yt-dlp", "-U"], check=True)  # עדכון אוטומטי
    except Exception as e:
        print("Error updating yt-dlp:", e)

@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/download")
def download(url: str):
    ensure_yt_dlp_latest()

    # הגדרות הורדה ל-MP3
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': '/tmp/%(title)s.%(ext)s',  # קובץ זמני
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            filename = ydl.prepare_filename(info).replace(".webm", ".mp3").replace(".m4a", ".mp3")
        return {"title": info.get("title"), "file": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# **החלק הקריטי ל-Fly**: מאזין לפורט מהסביבה
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
