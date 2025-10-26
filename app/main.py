# app/main.py
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from app.model import normalise_title
from app.metrics import router as metrics_router, metrics_middleware, BATCH_SIZE

app = FastAPI(title="TV Title Normalisation Service", version="1.0")
app = metrics_middleware(app)  # 注册指标中间件
app.include_router(metrics_router)

class SingleTitleRequest(BaseModel):
    messy_title: str

class BatchTitleRequest(BaseModel):
    messy_titles: List[str]

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.post("/normalise")
def normalise_single(request: SingleTitleRequest):
    return {"clean_title": normalise_title(request.messy_title)}

@app.post("/normalise-batch")
def normalise_batch(request: BatchTitleRequest):
    BATCH_SIZE.observe(len(request.messy_titles))
    clean = [normalise_title(t) for t in request.messy_titles]
    return {"clean_titles": clean}
