import os
import sys
import json
import time
import logging
from typing import Dict, Any, List, Tuple
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

from producer.app.eeg_loader import EEGLoader
from producer.app.window_extractor import EEGWindowExtractor
from spark.jobs.feature_extraction import EEGFeatureExtractor
from spark.jobs.signal_preprocessing import SignalPreprocessor
try:
    from .feature_schema import FEATURE_NAMES, TARGET_CLASSES
    from .evaluate import evaluate_classifier
except ImportError:
    from ml.feature_schema import FEATURE_NAMES, TARGET_CLASSES
    from ml.evaluate import evaluate_classifier

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("neurostream-ml-trainer")

def load_training_dataset(data_dir: str) -> Tuple[np.ndarray, np.ndarray, List[Dict[str, Any]]]:
    """
    Scans raw data directory for downloaded PhysioNet EDF files,
    segments them into windows, filters signals, and extracts feature vectors.
    """
    logger.info(f"Scanning dataset in {data_dir}...")
    manifest_path = os.path.join(data_dir, "manifest.json")
    
    files_to_load = []
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, "r") as f:
                manifest = json.load(f)
                for fname, info in manifest.get("files", {}).items():
                    if info.get("valid") and os.path.exists(info.get("path", "")):
                        files_to_load.append(info)
        except Exception:
            pass

    # Fallback to direct directory scan
    if not files_to_load:
        for root, _, files in os.walk(data_dir):
            for file in files:
                if file.endswith(".edf"):
                    path = os.path.join(root, file)
                    subject = os.path.basename(root)
                    run = file.replace(subject, "").replace(".edf", "")
                    files_to_load.append({"participant": subject, "run": run, "path": path})

    if not files_to_load:
        raise FileNotFoundError(f"No valid EDF files found in {data_dir}. Run scripts/download_dataset.py first.")

    logger.info(f"Found {len(files_to_load)} EDF recordings for feature extraction.")

    all_features = []
    all_labels = []
    window_metadata = []

    for file_info in files_to_load:
        edf_path = file_info["path"]
        participant = file_info["participant"]
        run = file_info["run"]
        recording_id = f"{participant}{run}"

        try:
            rec = EEGLoader.load_recording(edf_path, apply_filter=True, low_cut=0.5, high_cut=45.0)
            windows = EEGWindowExtractor.extract_windows(
                recording_info=rec,
                participant_id=participant,
                recording_id=recording_id,
                window_duration=2.0,
                window_overlap=0.5
            )

            for w in windows:
                win_data = np.array(w["data"], dtype=np.float64)
                filtered = SignalPreprocessor.bandpass_filter(win_data, sfreq=w["sampling_rate"], low_cut=0.5, high_cut=45.0)
                feat = EEGFeatureExtractor.extract_features(filtered, channel_names=w["channel_names"], sfreq=w["sampling_rate"])

                all_features.append(feat["feature_vector"])
                all_labels.append(w["original_label"])
                window_metadata.append({
                    "window_id": w["window_id"],
                    "participant": participant,
                    "recording": recording_id,
                    "label": w["original_label"]
                })
        except Exception as e:
            logger.error(f"Error loading {edf_path}: {e}")

    X = np.array(all_features, dtype=np.float64)
    y = np.array(all_labels, dtype=object)
    logger.info(f"Dataset extracted: {X.shape[0]} windows, {X.shape[1]} features per window.")
    return X, y, window_metadata

def train_model(
    data_dir: str = None,
    models_dir: str = None,
    n_estimators: int = 100,
    test_size: float = 0.25,
    random_state: int = 42
) -> Dict[str, Any]:
    data_dir = data_dir or os.getenv("DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "data", "raw"))
    models_dir = models_dir or os.getenv("MODELS_DIR", os.path.join(os.path.dirname(__file__), "..", "data", "models"))
    os.makedirs(models_dir, exist_ok=True)

    print("=" * 60)
    print(" NeuroStream Random Forest Model Training")
    print(f" Source Data: {data_dir}")
    print(f" Output Models: {models_dir}")
    print(f" Classes: {TARGET_CLASSES}")
    print("=" * 60)

    # 1. Load dataset & extract features
    X, y, metadata = load_training_dataset(data_dir)

    # Validate class presence
    unique_labels, counts = np.unique(y, return_counts=True)
    label_dist = dict(zip(unique_labels, counts))
    print(f"Class distribution: {label_dist}")

    # 2. Train / Test Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=test_size,
        random_state=random_state,
        stratify=y if len(unique_labels) > 1 else None
    )
    print(f"Training set: {X_train.shape[0]} samples, Test set: {X_test.shape[0]} samples.")

    # 3. Train Random Forest Classifier
    print(f"Training Random Forest (n_estimators={n_estimators}, class_weight='balanced')...")
    start_train = time.time()
    clf = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=16,
        min_samples_split=4,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=random_state,
        n_jobs=-1
    )
    clf.fit(X_train, y_train)
    train_duration = round(time.time() - start_train, 2)
    print(f"Model training completed in {train_duration}s.")

    # 4. Model Evaluation on Unseen Test Data
    y_pred = clf.predict(X_test)
    metrics = evaluate_classifier(list(y_test), list(y_pred), classes=TARGET_CLASSES)
    
    print("-" * 60)
    print(f"Accuracy:  {metrics['accuracy'] * 100:.2f}%")
    print(f"Precision: {metrics['precision_macro']:.4f}")
    print(f"Recall:    {metrics['recall_macro']:.4f}")
    print(f"F1-Score:  {metrics['f1_macro']:.4f}")
    print("Confusion Matrix:")
    for row_cls, row in zip(TARGET_CLASSES, metrics["confusion_matrix"]):
        print(f"  {row_cls:12}: {row}")
    print("-" * 60)

    # Feature Importance Analysis
    importances = clf.feature_importances_
    top_indices = np.argsort(importances)[::-1][:10]
    top_features = [{"feature": FEATURE_NAMES[i], "importance": round(float(importances[i]), 4)} for i in top_indices]
    print("Top 10 Important Features:")
    for tf in top_features:
        print(f"  {tf['feature']:25}: {tf['importance']:.4f}")

    # 5. Persist Model and Metadata
    version = f"v{int(time.time())}"
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    model_metadata = {
        "version": version,
        "algorithm": "RandomForestClassifier",
        "n_estimators": n_estimators,
        "classes": TARGET_CLASSES,
        "n_features": len(FEATURE_NAMES),
        "feature_names": FEATURE_NAMES,
        "training_timestamp": timestamp,
        "training_duration_sec": train_duration,
        "training_samples": int(X_train.shape[0]),
        "test_samples": int(X_test.shape[0]),
        "class_distribution": {str(k): int(v) for k, v in label_dist.items()},
        "metrics": metrics,
        "top_features": top_features,
        "disclaimer": "Academic & Research Big Data Analytics Platform. Not for clinical diagnosis."
    }

    # Save joblib bundle
    model_save_path = os.path.join(models_dir, "latest_model.joblib")
    meta_save_path = os.path.join(models_dir, "model_metadata.json")
    
    bundle = {
        "model": clf,
        "metadata": model_metadata
    }
    joblib.dump(bundle, model_save_path)
    with open(meta_save_path, "w") as f:
        json.dump(model_metadata, f, indent=2)

    print("=" * 60)
    print(f"Model saved to:    {model_save_path}")
    print(f"Metadata saved to: {meta_save_path}")
    print("=" * 60)
    return model_metadata

if __name__ == "__main__":
    train_model()

