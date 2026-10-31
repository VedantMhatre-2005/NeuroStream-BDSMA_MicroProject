import os
import pytest
import numpy as np

from ml.model_loader import is_model_trained, load_model_and_metadata
from spark.jobs.inference import StreamingInference
from ml.feature_schema import FEATURE_DIM, TARGET_CLASSES

def test_model_loading():
    models_dir = "/app/data/models"
    assert is_model_trained(models_dir) is True

    model, metadata = load_model_and_metadata(models_dir)
    assert model is not None
    assert metadata["algorithm"] == "RandomForestClassifier"
    assert len(metadata["classes"]) == 3
    assert metadata["metrics"]["accuracy"] > 0.0
    assert "confusion_matrix" in metadata["metrics"]

def test_streaming_inference():
    models_dir = "/app/data/models"
    model_path = os.path.join(models_dir, "latest_model.joblib")
    
    engine = StreamingInference(model_path=model_path)
    assert engine.model is not None

    # Create dummy 32-dimensional feature vector
    sample_feat = [0.5] * FEATURE_DIM
    pred_class, prob_map, conf = engine.predict(sample_feat)

    assert pred_class in TARGET_CLASSES
    assert conf > 0.0 and conf <= 1.0
    assert set(prob_map.keys()) == set(TARGET_CLASSES)
    assert pytest.approx(sum(prob_map.values()), abs=1e-2) == 1.0

