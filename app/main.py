from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from typing import List
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time

app = FastAPI(title="Cloud Ready API", version="1.0.0")

# ---- Prometheus metrics ----
REQUEST_COUNT = Counter(
    "cloud_ready_api_request_count",
    "Total HTTP requests",
    ["method", "endpoint", "http_status"],
)

REQUEST_LATENCY = Histogram(
    "cloud_ready_api_request_latency_seconds",
    "HTTP request latency",
    ["endpoint"],
)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    elapsed = time.time() - start_time

    endpoint = request.url.path
    REQUEST_LATENCY.labels(endpoint=endpoint).observe(elapsed)
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=endpoint,
        http_status=response.status_code,
    ).inc()

    return response


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/items")
def get_items() -> List[dict]:
    return [
        {"id": 1, "name": "Laptop", "price": 1200},
        {"id": 2, "name": "Headphones", "price": 80},
        {"id": 3, "name": "Mouse", "price": 25},
    ]


@app.get("/metrics")
def metrics():
    """Prometheus scrape endpoint"""
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)








# from fastapi import FastAPI
# from typing import List

# app = FastAPI(title="Cloud Ready API", version="1.0.0")


# @app.get("/health")
# def health():
#     return {"status": "ok"}


# @app.get("/items")
# def get_items() -> List[dict]:
#     return [
#         {"id": 1, "name": "Laptop", "price": 1200},
#         {"id": 2, "name": "Headphones", "price": 80},
#         {"id": 3, "name": "Mouse", "price": 25},
#     ]
