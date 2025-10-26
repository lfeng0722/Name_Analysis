from typing import List
from fastapi import FastAPI
from pydantic import BaseModel
from app.model import normalise_title
from app.metrics import metrics_middleware, metrics_endpoint, BATCH_SIZE

app = FastAPI(title="TV Title Normalisation Service", version="1.0")

# Attach metrics middleware
app.middleware("http")(metrics_middleware)

# ---------- Schemas (Pydantic) ----------

class SingleTitleRequest(BaseModel):
    messy_title: str

class BatchTitleRequest(BaseModel):
    messy_titles: List[str]

# ---------- Health & Metrics ----------

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.get("/metrics")
def get_metrics():
    return metrics_endpoint()

# ---------- API Endpoints ----------

@app.post("/normalise")
def normalise_single(payload: SingleTitleRequest):
    """
    Single-title normalisation.
    Input: {"messy_title": "..."}
    Output: {"clean_title": "..."}
    """
    clean = normalise_title(payload.messy_title)
    return {"clean_title": clean}

@app.post("/normalise-batch")
def normalise_batch(payload: BatchTitleRequest):
    """
    Batch-title normalisation.
    Input: {"messy_titles": ["...", "..."]}
    Output: {"clean_titles": ["...", "..."]}
    """
    titles = payload.messy_titles or []
    BATCH_SIZE.observe(len(titles))
    clean_titles = [normalise_title(t) for t in titles]
    return {"clean_titles": clean_titles}
