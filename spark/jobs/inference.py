import os
import logging
from typing import Dict, Any, Optional, Tuple
import joblib
import numpy as np

logger = logging.getLogger("neurostream-inference")

class StreamingInference:
    """
    Loads trained Random Forest model and generates real-time predictions with probabilities.
    """
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or os.getenv("MODEL_PATH", "/app/data/models/latest_model.joblib")
        self.model = None
        self.model_metadata = None
        self.load_model()

    def load_model(self) -> bool:
        if os.path.exists(self.model_path):
            try:
                bundle = joblib.load(self.model_path)
                if isinstance(bundle, dict) and "model" in bundle:
                    self.model = bundle["model"]
                    self.model_metadata = bundle.get("metadata", {})
                else:
                    self.model = bundle
                    self.model_metadata = {}
                logger.info(f"Loaded trained model from {self.model_path}")
                return True
            except Exception as e:
                logger.error(f"Failed to load model from {self.model_path}: {e}")
                self.model = None
                return False
        return False

    def predict(self, feature_vector: list) -> Tuple[Optional[str], Dict[str, float], float]:
        """
        Returns (predicted_class, class_probabilities, confidence)
        """
        if self.model is None:
            # Recheck if model has been trained recently
            if not self.load_model():
                return None, {}, 0.0

        try:
            x = np.array(feature_vector, dtype=np.float64).reshape(1, -1)
            probs = self.model.predict_proba(x)[0]
            classes = self.model.classes_

            prob_map = {str(cls_name): round(float(p), 4) for cls_name, p in zip(classes, probs)}
            best_idx = int(np.argmax(probs))
            predicted_class = str(classes[best_idx])
            confidence = round(float(probs[best_idx]), 4)

            return predicted_class, prob_map, confidence
        except Exception as e:
            logger.error(f"Inference error: {e}")
            return None, {}, 0.0

