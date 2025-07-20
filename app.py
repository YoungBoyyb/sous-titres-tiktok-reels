from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import whisper
import tempfile
import subprocess
import os

app = FastAPI()
model = whisper.load_model("base")

@app.post("/")
async def process_video(file: UploadFile = File(...)):
    if not file.filename.endswith(".mp4"):
        raise HTTPException(status_code=400, detail="Only .mp4 files are supported.")

    # Sauvegarde temporaire de la vidéo
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
        content = await file.read()
        temp_video.write(content)
        video_path = temp_video.name

    # Transcription avec Whisper (en français)
    result = model.transcribe(video_path, language="fr")

    # Création fichier .srt des sous-titres
    srt_path = video_path.replace(".mp4", ".srt")
    with open(srt_path, "w", encoding="utf-8") as srt_file:
        for i, segment in enumerate(result["segments"]):
            start = segment["start"]
            end = segment["end"]
            text = segment["text"].strip()
            srt_file.write(f"{i + 1}\n")
            srt_file.write(f"{int(start//60):02d}:{int(start%60):02d},000 --> {int(end//60):02d}:{int(end%60):02d},000\n")
            srt_file.write(f"{text}\n\n")

    # Génération du chemin de sortie vidéo subtitrée
    output_path = video_path.replace(".mp4", "_sub.mp4")

    # Commande ffmpeg pour incruster les sous-titres
    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-i", video_path,
        "-vf", f"subtitles={srt_path}:force_style='Fontsize=30,PrimaryColour=&H00FFFF&'",
        output_path
    ]

    try:
        subprocess.run(ffmpeg_cmd, check=True)
    except subprocess.CalledProcessError as e:
        # Nettoyage fichiers temporaires en cas d'erreur
        os.remove(video_path)
        os.remove(srt_path)
        raise HTTPException(status_code=500, detail=f"ffmpeg error: {e}")

    # Nettoyage fichiers temporaires d'origine (la vidéo source et srt)
    os.remove(video_path)
    os.remove(srt_path)

    # Retour du fichier vidéo subtitré
    return FileResponse(output_path, filename="video_sous_titres.mp4", media_type="video/mp4")
