FROM python:3.11-slim

# התקנת ffmpeg ל-MP3
RUN apt-get update && apt-get install -y ffmpeg

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .

# פורט שהשרת מאזין עליו
ENV PORT=8080
CMD ["python", "app.py"]
