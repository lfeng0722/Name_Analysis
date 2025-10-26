"""
metrics.py
-----------
Prometheus metrics integration for FastAPI.

This module defines request-level metrics (latency, count) and
domain-specific metrics (batch size). It also provides the middleware
and the /metrics endpoint for Prometheus scraping.
"""

from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
from fastapi import Request
import time

# ------------------------
# Metric definitions
# ------------------------

# Histogram for request latency (seconds)
REQ_LATENCY = Histogram(
    "http_request_latency_seconds",
    "Request latency in seconds",
    ["route", "method"],
    buckets=(0.05, 0.1, 0.2, 0.5, 1, 2, 5)
)

# Counter for total requests
REQ_COUNT = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["route", "method", "status"]
)

# Histogram for batch sizes in /normalise-batch
BATCH_SIZE = Histogram(
    "batch_size",
    "Size of batch payloads in normalise-batch endpoint",
    buckets=(1, 5, 10, 20, 50, 100, 500, 1000)
)

# ------------------------
# Middleware for recording metrics
# ------------------------

async def metrics_middleware(request: Request, call_next):
    """
    Middleware to measure and record latency, count, and status code of each request.
    """
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time

    route = request.url.path
    method = request.method
    status_code = str(response.status_code)

    REQ_LATENCY.labels(route=route, method=method).observe(process_time)
    REQ_COUNT.labels(route=route, method=method, status=status_code).inc()

    return response

# ------------------------
# Endpoint to expose metrics
# ------------------------

def metrics_endpoint():
    """
    Return all Prometheus metrics in text format for scraping.
    """
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
