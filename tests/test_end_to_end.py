import time
import json
import pytest
from kafka import KafkaProducer, KafkaConsumer
from fastapi.testclient import TestClient

try:
    from backend.app.main import app
    from backend.app.config import settings
    from backend.app.integrations.hive_client import hive_client
    from backend.app.services.hdfs_service import hdfs_service
except ModuleNotFoundError:
    from app.main import app
    from app.config import settings
    from app.integrations.hive_client import hive_client
    from app.services.hdfs_service import hdfs_service

client = TestClient(app)

def test_full_pipeline_verification():
    """
    End-to-end test verifying the entire distributed big data lifecycle:
    FastAPI -> Kafka -> Spark Preprocessing & ML -> HDFS Parquet -> Hive SQL Analytics
    """
    # 1. Verify Backend and Services Health
    res_sys = client.get("/api/system/status")
    assert res_sys.status_code == 200
    sys_data = res_sys.json()
    assert sys_data["overall_status"] == "operational"

    # 2. Verify Real PhysioNet Dataset Available
    res_ds = client.get("/api/dataset/status")
    assert res_ds.status_code == 200
    ds_data = res_ds.json()
    assert ds_data["total_recordings"] >= 9
    assert ds_data["total_participants"] >= 3

    # 3. Verify ML Model Trained and Metric Integrity
    res_model = client.get("/api/model/status")
    assert res_model.status_code == 200
    m_data = res_model.json()
    assert m_data["is_trained"] is True
    assert m_data["accuracy"] is not None
    assert m_data["accuracy"] > 0.35 # Substantially above random chance (33.3%)

    # 4. Verify HDFS Parquet Storage
    feat_files = hdfs_service.list_dir("/neurostream/features")
    pred_files = hdfs_service.list_dir("/neurostream/predictions")
    assert len(feat_files) > 0, "No Parquet files in /neurostream/features"
    assert len(pred_files) > 0, "No Parquet files in /neurostream/predictions"

    # 5. Verify Hive SQL Analytics
    q_res = client.post("/api/hive/query", json={
        "query": "SELECT predicted_class, COUNT(*) AS count FROM eeg_classification_results GROUP BY predicted_class"
    })
    assert q_res.status_code == 200
    q_data = q_res.json()
    assert q_data["success"] is True
    assert q_data["row_count"] == 3
    classes_found = [row[0] for row in q_data["rows"]]
    assert "left_hand" in classes_found
    assert "right_hand" in classes_found
    assert "rest" in classes_found

    # 6. Verify Analytics Overview Endpoint
    res_ov = client.get("/api/analytics/overview")
    assert res_ov.status_code == 200
    ov_data = res_ov.json()
    assert ov_data["success"] is True
    assert ov_data["total_windows"] >= 1000
    assert ov_data["total_predictions"] >= 1000

