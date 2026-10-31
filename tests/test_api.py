import pytest
from fastapi.testclient import TestClient

try:
    from backend.app.main import app
except ModuleNotFoundError:
    from app.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["project"] == "NeuroStream"
    assert data["status"] == "online"

def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_system_status():
    response = client.get("/api/system/status")
    assert response.status_code == 200
    data = response.json()
    assert "overall_status" in data
    assert "services" in data
    assert "kafka" in data["services"]
    assert "hive" in data["services"]
    assert "hdfs" in data["services"]
    assert "spark" in data["services"]

def test_dataset_status():
    response = client.get("/api/dataset/status")
    assert response.status_code == 200
    data = response.json()
    assert data["total_recordings"] >= 9
    assert data["total_participants"] >= 3

def test_dataset_participants():
    response = client.get("/api/dataset/participants")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3

def test_streaming_status():
    response = client.get("/api/streaming/status")
    assert response.status_code == 200
    data = response.json()
    assert "state" in data

def test_model_status():
    response = client.get("/api/model/status")
    assert response.status_code == 200
    data = response.json()
    assert data["is_trained"] is True
    assert "accuracy" in data

def test_analytics_overview():
    response = client.get("/api/analytics/overview")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["total_windows"] >= 1000

def test_hive_status_and_query():
    # 1. Hive Status
    res_status = client.get("/api/hive/status")
    assert res_status.status_code == 200
    assert res_status.json()["status"] == "connected"

    # 2. Hive Query
    res_query = client.post("/api/hive/query", json={"query": "SELECT COUNT(*) AS total FROM eeg_window_features"})
    assert res_query.status_code == 200
    data = res_query.json()
    assert data["success"] is True
    assert data["row_count"] == 1
    assert data["rows"][0][0] >= 1000

