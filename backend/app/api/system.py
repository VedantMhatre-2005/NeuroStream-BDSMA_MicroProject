import socket
import os
import psutil
from fastapi import APIRouter
from typing import Dict, Any

try:
    from backend.app.config import settings
    from backend.app.schemas.api_schemas import SystemStatusResponse, ResourceUsage
except ModuleNotFoundError:
    from app.config import settings
    from app.schemas.api_schemas import SystemStatusResponse, ResourceUsage

router = APIRouter(prefix="/api/system", tags=["System"])

def check_tcp(host: str, port: int, timeout: float = 1.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False

@router.get("/status", response_model=SystemStatusResponse)
def get_system_status():
    kafka_host, kafka_port = settings.KAFKA_BOOTSTRAP_SERVERS.split(":")
    hive_host = settings.HIVE_HOST
    hive_port = settings.HIVE_PORT

    services = {
        "kafka": {
            "status": "connected" if check_tcp(kafka_host, int(kafka_port)) else "disconnected",
            "endpoint": settings.KAFKA_BOOTSTRAP_SERVERS
        },
        "hive": {
            "status": "connected" if check_tcp(hive_host, hive_port) else "disconnected",
            "endpoint": f"{hive_host}:{hive_port}"
        },
        "hdfs": {
            "status": "connected" if check_tcp("namenode", 9000) else "disconnected",
            "endpoint": "namenode:9000"
        },
        "spark": {
            "status": "connected" if check_tcp("spark-master", 7077) else "disconnected",
            "endpoint": "spark-master:7077"
        }
    }
    overall = "operational" if all(s["status"] == "connected" for s in services.values()) else "degraded"
    return {
        "overall_status": overall,
        "services": services
    }

@router.get("/resources", response_model=ResourceUsage)
def get_resource_usage():
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    return {
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "memory_percent": mem.percent,
        "memory_used_mb": round(mem.used / (1024 * 1024), 2),
        "memory_total_mb": round(mem.total / (1024 * 1024), 2),
        "disk_percent": disk.percent
    }

