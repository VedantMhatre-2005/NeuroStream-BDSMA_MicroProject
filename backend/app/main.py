import socket
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from backend.app.config import settings
    from backend.app.api import system, dataset, streaming, model, analytics, hive
    from backend.app.websocket.live import websocket_endpoint
except ModuleNotFoundError:
    from app.config import settings
    from app.api import system, dataset, streaming, model, analytics, hive
    from app.websocket.live import websocket_endpoint

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("neurostream-api")

app = FastAPI(
    title="NeuroStream API",
    description="Real-Time EEG Brain-State Classification and Big Data Analytics",
    version="1.0.0"
)

# Enable CORS for React frontend (Vite runs on port 3000 / 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(system.router)
app.include_router(dataset.router)
app.include_router(streaming.router)
app.include_router(model.router)
app.include_router(analytics.router)
app.include_router(hive.router)

# WebSocket Endpoint for live EEG & predictions stream
app.add_api_websocket_route("/ws/live", websocket_endpoint)

@app.get("/")
def read_root():
    return {
        "project": "NeuroStream",
        "description": "Real-Time EEG Brain-State Classification & Big Data Analytics",
        "status": "online",
        "version": "1.0.0",
        "endpoints": {
            "health": "/api/health",
            "system_status": "/api/system/status",
            "dataset": "/api/dataset/status",
            "streaming": "/api/streaming/status",
            "model": "/api/model/status",
            "analytics": "/api/analytics/overview",
            "hive": "/api/hive/status",
            "websocket": "/ws/live",
            "docs": "/docs"
        }
    }

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "fastapi-backend",
        "version": "1.0.0"
    }
