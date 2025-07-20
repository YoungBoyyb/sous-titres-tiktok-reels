from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import whisper
import tempfile
import subprocess

app = FastAPI()
model = whisper.load_model("base")

@app.post("/")
async def process_video(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
        temp_video.write(await file.read())
        video_path = temp_video.name

    result = model.transcribe(video_path, language="fr")
    srt_path = video_path.replace(".mp4", ".srt")
    with open(srt_path, "w", encoding="utf-8") as srt:
        for i, seg in enumerate(result['segments']):
            start = seg['start']
            end = seg['end']
            text = seg['text']
            srt.write(f"{i+1}\n{int(start//60):02d}:{int(start%60):02d},000 --> {int(end//60):02d}:{int(end%60):02d},000\n{text}\n\n")

    output_path = video_path.replace(".mp4", "_sub.mp4")
    ffmpeg_cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vf", f"subtitles={srt_path}:force_style='Fontsize=30,PrimaryColour=&H00FFFF&'",
        output_path
    ]
    subprocess.run(ffmpeg_cmd, check=True)
    return FileResponse(output_path, filename="video_sous_titres.mp4", media_type="video/mp4")
