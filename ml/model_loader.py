import os
import json
import logging
from typing import Dict, Any, Optional, Tuple
import joblib

logger = logging.getLogger("neurostream-model-loader")

DEFAULT_MODEL_PATH = os.getenv("MODEL_PATH", "/app/data/models/latest_model.joblib")
DEFAULT_METADATA_PATH = os.getenv("MODEL_METADATA_PATH", "/app/data/models/model_metadata.json")

def get_model_paths(models_dir: Optional[str] = None) -> Tuple[str, str]:
    if models_dir is None:
        models_dir = os.getenv("MODELS_DIR", os.path.join(os.path.dirname(__file__), "..", "data", "models"))
    model_path = os.path.join(models_dir, "latest_model.joblib")
    meta_path = os.path.join(models_dir, "model_metadata.json")
    return model_path, meta_path

def is_model_trained(models_dir: Optional[str] = None) -> bool:
    model_path, _ = get_model_paths(models_dir)
    return os.path.exists(model_path) and os.path.getsize(model_path) > 1000

def load_model_and_metadata(models_dir: Optional[str] = None) -> Tuple[Any, Dict[str, Any]]:
    model_path, meta_path = get_model_paths(models_dir)
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Trained model not found at: {model_path}")
    
    bundle = joblib.load(model_path)
    if isinstance(bundle, dict) and "model" in bundle:
        model = bundle["model"]
        metadata = bundle.get("metadata", {})
    else:
        model = bundle
        metadata = {}

    if not metadata and os.path.exists(meta_path):
        try:
            with open(meta_path, "r") as f:
                metadata = json.load(f)
        except Exception:
            pass

    return model, metadata

