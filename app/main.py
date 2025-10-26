"""
main.py
--------
Main FastAPI application entry point.

Includes:
- /healthz for health checks
- /normalise and /normalise-batch endpoints
- /metrics for Prometheus monitoring
"""

from fastapi import FastAPI, Request
from app.model import normalise_title
from app.metrics import metrics_middleware, metrics_endpoint, BATCH_SIZE

app = FastAPI(title="TV Title Normalisation Service", version="1.0")

# Attach metrics middleware
app.middleware("http")(metrics_middleware)

# ------------------------
# Health check
# ------------------------

@app.get("/healthz")
def healthz():
    """
    Lightweight endpoint for container/K8s health probes.
    """
    return {"status": "ok"}

# ------------------------
# Normalisation endpoints
# ------------------------

@app.post("/normalise")
def normalise_single(request: dict):
    """
    Single-title normalisation.
    Input: {"messy_title": "..."}
    Output: {"clean_title": "..."}
    """
    messy_title = request.get("messy_title")
    clean = normalise_title(messy_title)
    return {"clean_title": clean}


@app.post("/normalise-batch")
def normalise_batch(request: dict):
    """
    Batch-title normalisation.
    Input: {"messy_titles": ["...", "..."]}
    Output: {"clean_titles": ["...", "..."]}
    Also records batch size metric.
    """
    messy_titles = request.get("messy_titles", [])
    BATCH_SIZE.observe(len(messy_titles))
    clean_titles = [normalise_title(t) for t in messy_titles]
    return {"clean_titles": clean_titles}

# ------------------------
# Metrics endpoint
# ------------------------

@app.get("/metrics")
def get_metrics():
    """
    Expose application and Python runtime metrics for Prometheus.
    """
    return metrics_endpoint()
