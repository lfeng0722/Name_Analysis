from typing import List
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.model import normalise_title
from app.metrics import metrics_middleware, metrics_endpoint, BATCH_SIZE

app = FastAPI(title="TV Title Normalisation Service", version="1.0")

# 指标中间件
app.middleware("http")(metrics_middleware)

# （可保留，也无妨）兜底异常处理
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": str(exc)})

# --------- Pydantic Schemas ---------
class SingleTitleRequest(BaseModel):
    messy_title: str

class BatchTitleRequest(BaseModel):
    messy_titles: List[str]

# --------- Health & Metrics ----------
@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.get("/metrics")
def get_metrics():
    return metrics_endpoint()

# --------- API Endpoints -------------
@app.post("/normalise")
def normalise_single(payload: SingleTitleRequest):
    """
    Expected 500 when model raises (tests monkeypatch normalise_title to raise).
    """
    try:
        clean = normalise_title(payload.messy_title)
        return {"clean_title": clean}
    except Exception as e:
        # 显式转成 500，避免异常冒泡到 TestClient
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.post("/normalise-batch")
def normalise_batch(payload: BatchTitleRequest):
    """
    Expected 500 when any item triggers model failure (tests monkeypatch).
    """
    titles = payload.messy_titles or []
    BATCH_SIZE.observe(len(titles))
    try:
        clean_titles = [normalise_title(t) for t in titles]
        return {"clean_titles": clean_titles}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
