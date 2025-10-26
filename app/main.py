from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel
from typing import List
from app.model import normalise_title
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time

app = FastAPI(title="TV Title Normalisation Service", version="1.0")

# Prometheus metrics
REQUEST_COUNTER = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path", "status"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5),
)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    path = request.url.path
    method = request.method
    # Avoid self-scrape noise on /metrics if desired
    if path == "/metrics":
        return await call_next(request)

    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start
    status_code = str(response.status_code)
    REQUEST_COUNTER.labels(method=method, path=path, status=status_code).inc()
    REQUEST_LATENCY.labels(method=method, path=path, status=status_code).observe(duration)
    return response


class SingleTitleRequest(BaseModel):
    messy_title: str


class BatchTitleRequest(BaseModel):
    messy_titles: List[str]


@app.post("/normalise")
def normalise_single(request: SingleTitleRequest):
    try:
        clean_title = normalise_title(request.messy_title)
        return {"clean_title": clean_title}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/normalise-batch")
def normalise_batch(request: BatchTitleRequest):
    try:
        clean_titles = [normalise_title(t) for t in request.messy_titles]
        return {"clean_titles": clean_titles}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
def metrics() -> Response:
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
