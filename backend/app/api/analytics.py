import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query

try:
    from backend.app.integrations.hive_client import hive_client
except ModuleNotFoundError:
    from app.integrations.hive_client import hive_client

router = APIRouter(prefix="/api/analytics", tags=["Big Data Analytics"])
logger = logging.getLogger("analytics-api")

@router.get("/overview")
def get_analytics_overview():
    """
    Returns high-level analytical overview computed via Hive aggregations.
    """
    try:
        # Total windows per participant
        res_win = hive_client.get_windows_per_participant()
        # Predictions distribution
        res_pred = hive_client.get_brain_states_distribution()
        
        total_windows = sum(row[1] for row in res_win.get("rows", [])) if res_win.get("success") else 0
        total_participants = res_win.get("row_count", 0) if res_win.get("success") else 0
        
        predictions = {}
        total_predictions = 0
        for row in res_pred.get("rows", []):
            state, count, conf = row[0], row[1], row[2]
            predictions[state] = {"count": count, "avg_confidence": conf}
            total_predictions += count

        return {
            "success": True,
            "total_windows": total_windows,
            "total_participants": total_participants,
            "total_predictions": total_predictions,
            "predictions_by_state": predictions,
            "windows_by_participant": [
                {"participant_id": r[0], "total_windows": r[1]} for r in res_win.get("rows", [])
            ]
        }
    except Exception as e:
        logger.error(f"Error in analytics overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/brain-states")
def get_brain_states_distribution():
    res = hive_client.get_brain_states_distribution()
    if not res.get("success"):
        raise HTTPException(status_code=500, detail=res.get("error", "Hive query failed"))
    
    data = []
    for r in res.get("rows", []):
        data.append({
            "predicted_class": r[0],
            "count": r[1],
            "avg_confidence": r[2]
        })
    return {
        "success": True,
        "execution_time_ms": res.get("execution_time_ms"),
        "data": data
    }

@router.get("/channel-activity")
def get_channel_activity(limit: int = Query(20, ge=1, le=64)):
    res = hive_client.get_channel_activity(limit=limit)
    if not res.get("success"):
        raise HTTPException(status_code=500, detail=res.get("error", "Hive query failed"))

    data = []
    for r in res.get("rows", []):
        data.append({
            "channel_name": r[0],
            "avg_mean": r[1],
            "avg_variance": r[2],
            "avg_alpha": r[3],
            "avg_beta": r[4]
        })
    return {
        "success": True,
        "execution_time_ms": res.get("execution_time_ms"),
        "data": data
    }

@router.get("/band-power")
def get_band_power():
    res = hive_client.get_band_power_by_state()
    if not res.get("success"):
        raise HTTPException(status_code=500, detail=res.get("error", "Hive query failed"))

    data = []
    for r in res.get("rows", []):
        data.append({
            "predicted_class": r[0],
            "delta_power": r[1],
            "theta_power": r[2],
            "alpha_power": r[3],
            "beta_power": r[4],
            "gamma_power": r[5]
        })
    return {
        "success": True,
        "execution_time_ms": res.get("execution_time_ms"),
        "data": data
    }

@router.get("/participants")
def get_participant_analytics():
    res = hive_client.get_participant_predictions()
    if not res.get("success"):
        raise HTTPException(status_code=500, detail=res.get("error", "Hive query failed"))

    data = []
    for r in res.get("rows", []):
        data.append({
            "participant_id": r[0],
            "predicted_class": r[1],
            "count": r[2]
        })
    return {
        "success": True,
        "execution_time_ms": res.get("execution_time_ms"),
        "data": data
    }

@router.get("/timeline")
def get_timeline(limit: int = Query(30, ge=5, le=100)):
    res = hive_client.get_temporal_predictions(limit=limit)
    if not res.get("success"):
        raise HTTPException(status_code=500, detail=res.get("error", "Hive query failed"))

    data = []
    for r in res.get("rows", []):
        data.append({
            "time_minute": r[0],
            "predictions_count": r[1],
            "avg_latency_ms": r[2]
        })
    return {
        "success": True,
        "execution_time_ms": res.get("execution_time_ms"),
        "data": data
    }

@router.get("/recordings")
def get_recording_analytics():
    res = hive_client.get_predictions_by_recording()
    if not res.get("success"):
        raise HTTPException(status_code=500, detail=res.get("error", "Hive query failed"))

    data = []
    for r in res.get("rows", []):
        data.append({
            "recording_id": r[0],
            "total_predictions": r[1],
            "left_hand_count": r[2],
            "right_hand_count": r[3],
            "rest_count": r[4]
        })
    return {
        "success": True,
        "execution_time_ms": res.get("execution_time_ms"),
        "data": data
    }

