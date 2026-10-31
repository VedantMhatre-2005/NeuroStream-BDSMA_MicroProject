import datetime
from typing import Dict, Any, List
import numpy as np

class EEGWindowExtractor:
    """
    Segments continuous multi-channel EEG recordings into timestamped sliding windows.
    Assigns ground truth labels based on PhysioNet motor imagery event annotations.
    """

    @staticmethod
    def get_window_label(start_time: float, end_time: float, annotations: List[Dict[str, Any]]) -> str:
        """
        Determines the task label for a window based on annotations.
        Uses the annotation that covers the center point of the window.
        """
        mid_time = (start_time + end_time) / 2.0
        
        for annot in annotations:
            onset = annot["onset"]
            duration = annot["duration"]
            if onset <= mid_time <= (onset + duration):
                return annot["label"]

        # If window is before the first task or in baseline, default to rest
        return "rest"

    @classmethod
    def extract_windows(
        cls,
        recording_info: Dict[str, Any],
        participant_id: str,
        recording_id: str,
        window_duration: float = 2.0,
        window_overlap: float = 0.5,
        normalize: bool = False
    ) -> List[Dict[str, Any]]:
        sfreq = recording_info["sampling_rate"]
        data = recording_info["data"] # Shape: (n_channels, n_samples)
        channel_names = recording_info["channel_names"]
        annotations = recording_info.get("annotations", [])
        
        window_samples = int(window_duration * sfreq)
        step_samples = int(window_samples * (1.0 - window_overlap))
        if step_samples < 1:
            step_samples = 1

        total_samples = data.shape[1]
        windows = []
        window_idx = 0

        for start_idx in range(0, total_samples - window_samples + 1, step_samples):
            end_idx = start_idx + window_samples
            
            # Extract slice: (n_channels, window_samples)
            window_data = data[:, start_idx:end_idx]

            # Optional z-score normalization across the window per channel
            if normalize:
                means = np.mean(window_data, axis=1, keepdims=True)
                stds = np.std(window_data, axis=1, keepdims=True)
                stds[stds == 0] = 1.0
                window_data = (window_data - means) / stds

            start_time = float(start_idx) / sfreq
            end_time = float(end_idx) / sfreq
            
            label = cls.get_window_label(start_time, end_time, annotations)
            window_id = f"{recording_id}_W{window_idx:05d}"

            window_record = {
                "window_id": window_id,
                "participant_id": participant_id,
                "recording_id": recording_id,
                "channel_names": channel_names,
                "n_channels": len(channel_names),
                "n_samples": window_samples,
                "sampling_rate": sfreq,
                "start_time": round(start_time, 4),
                "end_time": round(end_time, 4),
                "original_label": label,
                "data": window_data.tolist(), # 2D array serialized as list of lists
                "ingestion_timestamp": datetime.datetime.utcnow().isoformat() + "Z"
            }
            windows.append(window_record)
            window_idx += 1

        return windows

