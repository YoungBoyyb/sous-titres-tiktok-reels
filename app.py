from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
import whisper
import tempfile
import subprocess
import os
import uuid
from typing import Dict

app = FastAPI()
model = whisper.load_model("tiny")  # Modèle léger pour tests rapides

# Stockage simple en mémoire des tâches
tasks: Dict[str, Dict] = {}

def process_video_task(task_id: str, video_path: str):
    try:
        # Transcription
        result = model.transcribe(video_path, language="fr")

        # Création du fichier SRT
        srt_path = video_path.replace(".mp4", ".srt")
        with open(srt_path, "w", encoding="utf-8") as srt_file:
            for i, segment in enumerate(result["segments"]):
                start = segment["start"]
                end = segment["end"]
                text = segment["text"].strip()
                srt_file.write(f"{i + 1}\n")
                srt_file.write(f"{int(start//60):02d}:{int(start%60):02d},000 --> {int(end//60):02d}:{int(end%60):02d},000\n")
                srt_file.write(f"{text}\n\n")

        # Sortie vidéo subtitrée
        output_path = video_path.replace(".mp4", "_sub.mp4")

        ffmpeg_cmd = [
            "ffmpeg",
            "-y",
            "-i", video_path,
            "-vf", f"subtitles={srt_path}:force_style='Fontsize=30,PrimaryColour=&H00FFFF&'",
            output_path
        ]

        subprocess.run(ffmpeg_cmd, check=True)

        # Nettoyage fichiers temporaires d'origine
        os.remove(video_path)
        os.remove(srt_path)

        # Mise à jour tâche
        tasks[task_id]["status"] = "done"
        tasks[task_id]["result_path"] = output_path

    except Exception as e:
        tasks[task_id]["status"] = "error"
        tasks[task_id]["error"] = str(e)

@app.post("/start")
async def start_process(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    if not file.filename.endswith(".mp4"):
        raise HTTPException(status_code=400, detail="Only .mp4 files are supported.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
        content = await file.read()
        temp_video.write(content)
        video_path = temp_video.name

    task_id = str(uuid.uuid4())
    tasks[task_id] = {"status": "processing", "result_path": None}

    # Lancer traitement en tâche de fond
    background_tasks.add_task(process_video_task, task_id, video_path)

    return {"task_id": task_id}

@app.get("/status/{task_id}")
def get_status(task_id: str):
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task["status"] == "done":
        return {"status": "done", "video_url": f"/download/{task_id}"}
    elif task["status"] == "error":
        return {"status": "error", "error": task.get("error")}
    else:
        return {"status": "processing"}

@app.get("/download/{task_id}")
def download_result(task_id: str):
    task = tasks.get(task_id)
    if not task or task["status"] != "done":
        raise HTTPException(status_code=404, detail="Result not available")

    return FileResponse(task["result_path"], filename="video_sous_titres.mp4", media_type="video/mp4")
