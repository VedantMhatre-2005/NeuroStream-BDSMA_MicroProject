from typing import Dict, Any, List
import numpy as np
from sklearn.metrics import (
    accuracy_score, precision_recall_fscore_support, confusion_matrix, classification_report
)

def evaluate_classifier(
    y_true: List[str],
    y_pred: List[str],
    classes: List[str] = None
) -> Dict[str, Any]:
    if classes is None:
        classes = ["left_hand", "right_hand", "rest"]

    acc = float(accuracy_score(y_true, y_pred))
    p_macro, r_macro, f1_macro, _ = precision_recall_fscore_support(
        y_true, y_pred, average="macro", zero_division=0
    )
    p_per, r_per, f1_per, support = precision_recall_fscore_support(
        y_true, y_pred, labels=classes, zero_division=0
    )
    
    cm = confusion_matrix(y_true, y_pred, labels=classes).tolist()

    per_class = {}
    for idx, cls_name in enumerate(classes):
        per_class[cls_name] = {
            "precision": round(float(p_per[idx]), 4),
            "recall": round(float(r_per[idx]), 4),
            "f1_score": round(float(f1_per[idx]), 4),
            "support": int(support[idx])
        }

    return {
        "accuracy": round(acc, 4),
        "precision_macro": round(float(p_macro), 4),
        "recall_macro": round(float(r_macro), 4),
        "f1_macro": round(float(f1_macro), 4),
        "per_class": per_class,
        "confusion_matrix": cm,
        "classes": classes,
        "total_samples": len(y_true)
    }

