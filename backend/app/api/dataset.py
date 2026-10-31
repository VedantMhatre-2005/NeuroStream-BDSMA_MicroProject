import os
import glob
import json
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Query, BackgroundTasks, HTTPException
import numpy as np

try:
    from backend.app.config import settings
    from backend.app.schemas.api_schemas import DownloadRequest, DatasetStatusResponse
except ModuleNotFoundError:
    from app.config import settings
    from app.schemas.api_schemas import DownloadRequest, DatasetStatusResponse

from producer.app.eeg_loader import EEGLoader

router = APIRouter(prefix="/api/dataset", tags=["Dataset"])
logger = logging.getLogger("dataset-api")

_download_in_progress = False

@router.get("/status")
def get_dataset_status():
    raw_dir = os.path.join(settings.DATA_DIR, "raw")
    manifest_path = os.path.join(raw_dir, "manifest.json")
    
    manifest = {}
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, "r") as f:
                manifest = json.load(f)
        except Exception as e:
            logger.error(f"Error reading manifest: {e}")

    edf_files = glob.glob(os.path.join(raw_dir, "*", "*.edf"))
    total_size_bytes = sum(os.path.getsize(f) for f in edf_files)
    participants = set(os.path.basename(os.path.dirname(f)) for f in edf_files)

    return {
        "total_participants": len(participants),
        "total_recordings": len(edf_files),
        "total_size_mb": round(total_size_bytes / (1024 * 1024), 2),
        "download_in_progress": _download_in_progress,
        "manifest": manifest
    }

@router.get("/participants")
def list_participants():
    raw_dir = os.path.join(settings.DATA_DIR, "raw")
    edf_files = glob.glob(os.path.join(raw_dir, "*", "*.edf"))
    
    participants_map = {}
    for f in edf_files:
        pid = os.path.basename(os.path.dirname(f))
        fname = os.path.basename(f)
        run = fname.replace(pid, "").replace(".edf", "")
        if pid not in participants_map:
            participants_map[pid] = []
        participants_map[pid].append({
            "run": run,
            "filename": fname,
            "size_kb": round(os.path.getsize(f) / 1024, 1)
        })

    return [
        {
            "participant_id": pid,
            "recording_count": len(runs),
            "recordings": sorted(runs, key=lambda x: x["run"])
        }
        for pid, runs in sorted(participants_map.items())
    ]

@router.get("/recordings")
def list_recordings():
    raw_dir = os.path.join(settings.DATA_DIR, "raw")
    edf_files = glob.glob(os.path.join(raw_dir, "*", "*.edf"))
    
    results = []
    for f in sorted(edf_files):
        pid = os.path.basename(os.path.dirname(f))
        fname = os.path.basename(f)
        run = fname.replace(pid, "").replace(".edf", "")
        results.append({
            "recording_id": f"{pid}_{run}",
            "participant_id": pid,
            "run": run,
            "filename": fname,
            "path": f,
            "size_bytes": os.path.getsize(f),
            "size_mb": round(os.path.getsize(f) / (1024 * 1024), 2)
        })
    return results

@router.get("/sample-signal")
def get_sample_signal(
    recording_id: Optional[str] = Query(None, description="e.g. S001_R04 or S001R04"),
    channels: Optional[str] = Query("Cz,C3,C4,Fc3,Fc4,Cp3,Cp4", description="Comma-separated channel names"),
    start_sec: float = Query(0.0, ge=0.0),
    duration_sec: float = Query(10.0, ge=0.5, le=60.0),
    filtered: bool = Query(True),
    downsample_factor: int = Query(2, ge=1, le=10)
):
    """
    Returns actual multi-channel EEG time-series for signal visualization.
    """
    raw_dir = os.path.join(settings.DATA_DIR, "raw")
    edf_files = glob.glob(os.path.join(raw_dir, "*", "*.edf"))
    if not edf_files:
        raise HTTPException(status_code=404, detail="No EEG recordings available.")

    selected_file = edf_files[0]
    if recording_id:
        target = recording_id.replace("_", "").lower()
        for f in edf_files:
            if target in os.path.basename(f).lower():
                selected_file = f
                break

    try:
        raw_info = EEGLoader.load_recording(selected_file, apply_filter=filtered)
        sfreq = raw_info["sampling_rate"]
        all_channels = raw_info["channel_names"]
        data_matrix = raw_info["data"] # (n_channels, n_samples)
        times = raw_info["times"]
        annotations = raw_info["annotations"]

        # Parse requested channels
        req_channels = [c.strip() for c in channels.split(",") if c.strip()]
        channel_indices = []
        valid_channels = []
        for ch in req_channels:
            if ch in all_channels:
                channel_indices.append(all_channels.index(ch))
                valid_channels.append(ch)

        if not valid_channels:
            # Fallback to first 5 channels
            valid_channels = all_channels[:5]
            channel_indices = list(range(len(valid_channels)))

        # Slice time window
        start_idx = int(start_sec * sfreq)
        end_idx = min(int((start_sec + duration_sec) * sfreq), data_matrix.shape[1])
        if start_idx >= data_matrix.shape[1]:
            start_idx = 0
            end_idx = min(int(duration_sec * sfreq), data_matrix.shape[1])

        # Slice data and downsample
        step = downsample_factor
        sliced_times = times[start_idx:end_idx:step].tolist()
        
        series = {}
        for ch_name, ch_idx in zip(valid_channels, channel_indices):
            ch_data = data_matrix[ch_idx, start_idx:end_idx:step]
            series[ch_name] = np.round(ch_data, 2).tolist()

        # Find annotations intersecting this window
        window_annots = []
        for a in annotations:
            a_end = a["onset"] + a["duration"]
            if not (a_end < start_sec or a["onset"] > (start_sec + duration_sec)):
                window_annots.append(a)

        return {
            "recording_file": os.path.basename(selected_file),
            "sampling_rate": sfreq / step,
            "original_sampling_rate": sfreq,
            "start_sec": start_sec,
            "duration_sec": duration_sec,
            "channels": valid_channels,
            "available_channels": all_channels,
            "timestamps": sliced_times,
            "signals": series,
            "annotations": window_annots
        }

    except Exception as e:
        logger.error(f"Error loading sample signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

