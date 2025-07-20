from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI()

class PredictRequest(BaseModel):
    data: List[str]

@app.get("/")
async def root():
    return {"message": "API OK"}

@app.post("/api/predict/")
async def predict(request: PredictRequest):
    # Renvoie simplement ce qui est reçu
    return {"received_data": request.data}
