from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
import yt_dlp
import os
import uuid

app = FastAPI()

# תיקיית אחסון זמנית
TEMP_DIR = "/tmp/yt_mp3"
os.makedirs(TEMP_DIR, exist_ok=True)

@app.get("/download_mp3")
async def download_mp3(url: str = Query(..., description="YouTube URL")):
    try:
        file_id = str(uuid.uuid4())
        output_template = os.path.join(TEMP_DIR, f"{file_id}.%(ext)s")
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_template,
            'quiet': True,
            'noplaylist': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            mp3_file = os.path.splitext(filename)[0] + ".mp3"
        
        return JSONResponse({
            "error": 0,
            "title": info.get("title"),
            "mp3_url": f"/files/{os.path.basename(mp3_file)}"
        })
    
    except Exception as e:
        return JSONResponse({"error": 1, "message": str(e)})

# להגיש קבצים סטטיים
from fastapi.staticfiles import StaticFiles
app.mount("/files", StaticFiles(directory=TEMP_DIR), name="files")
