from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.responses import FileResponse
import os
import yt_dlp
import uuid
import threading
import time

app = FastAPI()

# תיקייה זמנית לשמירת קבצים
TMP_DIR = "/tmp/yt-dlp-mp3"
os.makedirs(TMP_DIR, exist_ok=True)

# ניקוי קבצים ישנים (כל שעה)
def cleanup_old_files():
    while True:
        now = time.time()
        for f in os.listdir(TMP_DIR):
            path = os.path.join(TMP_DIR, f)
            if os.path.isfile(path) and now - os.path.getmtime(path) > 3600:
                try:
                    os.remove(path)
                except:
                    pass
        time.sleep(3600)

threading.Thread(target=cleanup_old_files, daemon=True).start()

# מודל JSON לבקשת API
class DownloadRequest(BaseModel):
    url: str

@app.post("/download")
async def download_mp3(req: DownloadRequest):
    yt_url = req.url
    file_id = str(uuid.uuid4())
    output_path = os.path.join(TMP_DIR, f"{file_id}.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_path,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "quiet": True,
        "no_warnings": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(yt_url, download=True)
            filename = ydl.prepare_filename(info).replace(".webm", ".mp3").replace(".m4a", ".mp3")
            title = info.get("title", "Unknown Title")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    mp3_url = f"/files/{os.path.basename(filename)}"
    return {"status": "ok", "title": title, "mp3_url": mp3_url}

@app.get("/files/{filename}")
async def serve_file(filename: str):
    path = os.path.join(TMP_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path, media_type="audio/mpeg", filename=filename)
