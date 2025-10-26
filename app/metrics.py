# app/metrics.py
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
from fastapi import Request
import time

__all__ = [
    "REQ_LATENCY",
    "REQ_COUNT",
    "BATCH_SIZE",
    "metrics_middleware",
    "metrics_endpoint",
]

# Request latency
REQ_LATENCY = Histogram(
    "http_request_latency_seconds",
    "Request latency in seconds",
    ["route", "method"],
    buckets=(0.05, 0.1, 0.2, 0.5, 1, 2, 5),
)

# Request count
REQ_COUNT = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["route", "method", "status"],
)

# Batch size for /normalise-batch
BATCH_SIZE = Histogram(
    "batch_size",
    "Size of batch payloads in normalise-batch endpoint",
    buckets=(1, 5, 10, 20, 50, 100, 500, 1000),
)

async def metrics_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - start

    route = request.url.path
    method = request.method
    status = str(response.status_code)

    REQ_LATENCY.labels(route=route, method=method).observe(elapsed)
    REQ_COUNT.labels(route=route, method=method, status=status).inc()
    return response

def metrics_endpoint():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
