import os
import json
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

try:
    from backend.app.config import settings
except ModuleNotFoundError:
    from app.config import settings

from ml.model_loader import is_model_trained, load_model_and_metadata, get_model_paths
from ml.train import train_model

router = APIRouter(prefix="/api/model", tags=["Machine Learning"])
logger = logging.getLogger("model-api")

_training_in_progress = False

class TrainRequest(BaseModel):
    n_estimators: int = 100
    test_size: float = 0.25
    random_state: int = 42

def _do_train(n_estimators: int, test_size: float, random_state: int):
    global _training_in_progress
    _training_in_progress = True
    try:
        data_dir = os.path.join(settings.DATA_DIR, "raw")
        models_dir = os.path.join(settings.DATA_DIR, "models")
        logger.info(f"Triggering model training with {n_estimators} trees...")
        train_model(
            data_dir=data_dir,
            output_dir=models_dir,
            n_estimators=n_estimators,
            test_size=test_size,
            random_state=random_state
        )
        logger.info("Model training completed successfully.")
    except Exception as e:
        logger.error(f"Error during training: {e}")
    finally:
        _training_in_progress = False

@router.get("/status")
def get_model_status():
    trained = is_model_trained(settings.MODELS_DIR)
    meta = {}
    if trained:
        try:
            _, meta = load_model_and_metadata(settings.MODELS_DIR)
        except Exception:
            pass

    acc = meta.get("metrics", {}).get("accuracy")
    if acc is None:
        acc = meta.get("evaluation_metrics", {}).get("accuracy")

    return {
        "is_trained": trained,
        "is_training": _training_in_progress,
        "version": meta.get("version", "v1.0" if trained else "none"),
        "trained_at": meta.get("training_timestamp"),
        "algorithm": meta.get("algorithm", "RandomForestClassifier"),
        "accuracy": acc,
        "total_samples": meta.get("total_samples", 0) or meta.get("training_samples", 0),
        "classes": meta.get("classes", ["left_hand", "right_hand", "rest"])
    }

@router.post("/train")
def trigger_training(req: TrainRequest, background_tasks: BackgroundTasks):
    global _training_in_progress
    if _training_in_progress:
        raise HTTPException(status_code=409, detail="Model training is already running in the background.")

    background_tasks.add_task(_do_train, req.n_estimators, req.test_size, req.random_state)
    return {
        "status": "training_started",
        "message": f"Random Forest training started with {req.n_estimators} estimators (test_size={req.test_size})."
    }

@router.get("/metrics")
def get_model_metrics():
    if not is_model_trained(settings.MODELS_DIR):
        raise HTTPException(status_code=404, detail="Model not yet trained.")
    _, meta = load_model_and_metadata(settings.MODELS_DIR)
    return meta

@router.get("/confusion-matrix")
def get_confusion_matrix():
    if not is_model_trained(settings.MODELS_DIR):
        raise HTTPException(status_code=404, detail="Model not yet trained.")
    _, meta = load_model_and_metadata(settings.MODELS_DIR)
    eval_m = meta.get("metrics", {}) or meta.get("evaluation_metrics", {})
    return {
        "classes": meta.get("classes", ["left_hand", "right_hand", "rest"]),
        "confusion_matrix": eval_m.get("confusion_matrix", []),
        "accuracy": eval_m.get("accuracy", 0.0),
        "class_report": eval_m.get("per_class", {}) or eval_m.get("class_report", {})
    }

@router.get("/features")
def get_feature_importances():
    if not is_model_trained(settings.MODELS_DIR):
        raise HTTPException(status_code=404, detail="Model not yet trained.")
    _, meta = load_model_and_metadata(settings.MODELS_DIR)
    return {
        "features": meta.get("top_features", []),
        "total_features": len(meta.get("feature_names", []))
    }
