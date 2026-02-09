from flask import Flask, request, jsonify, send_from_directory
import os
import yt_dlp
import uuid
import threading
import time

app = Flask(__name__)

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
        time.sleep(3600)  # בדיקה כל שעה

threading.Thread(target=cleanup_old_files, daemon=True).start()

# Endpoint API ל-GAS
@app.route("/download", methods=["POST"])
def download_mp3():
    data = request.get_json()
    if not data or "url" not in data:
        return jsonify({"status":"error","message":"Missing URL"}), 400

    yt_url = data["url"]
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
        return jsonify({"status":"error","message":str(e)}), 500

    # URL להורדה ישירה
    mp3_url = f"{request.url_root}files/{os.path.basename(filename)}"
    return jsonify({"status":"ok", "title": title, "mp3_url": mp3_url})

# Endpoint להורדת הקובץ
@app.route("/files/<path:filename>", methods=["GET"])
def serve_file(filename):
    return send_from_directory(TMP_DIR, filename, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
