import os
import re
from typing import Dict, Any, List, Optional
import numpy as np
import mne

# PhysioNet EEGMMIDB Motor Imagery Protocol (Runs 4, 8, 12):
# T0 = Rest
# T1 = Onset of Left fist motion (or imagery)
# T2 = Onset of Right fist motion (or imagery)
ANNOTATION_LABEL_MAP = {
    "T0": "rest",
    "T1": "left_hand",
    "T2": "right_hand"
}

def clean_channel_name(name: str) -> str:
    """Removes trailing dots or whitespace from EDF channel names."""
    return re.sub(r"[.\s]+$", "", name.strip())

class EEGLoader:
    """
    Loads and preprocesses real EDF/EDF+ recordings from PhysioNet.
    Extracts signals, sampling frequencies, channel designations, and annotations.
    """
    
    @staticmethod
    def load_recording(
        edf_path: str,
        apply_filter: bool = True,
        low_cut: float = 0.5,
        high_cut: float = 45.0,
        notch_freq: Optional[float] = 60.0
    ) -> Dict[str, Any]:
        if not os.path.exists(edf_path):
            raise FileNotFoundError(f"EEG file not found: {edf_path}")

        # Load EDF file using MNE
        raw = mne.io.read_raw_edf(edf_path, preload=True, verbose="ERROR")

        # Extract sampling rate
        sfreq = int(raw.info["sfreq"])
        
        # Clean channel names
        orig_ch_names = raw.info["ch_names"]
        clean_ch_names = [clean_channel_name(ch) for ch in orig_ch_names]

        # Power-line noise notch filter (if specified and valid)
        if apply_filter and notch_freq and notch_freq < sfreq / 2:
            try:
                raw.notch_filter(freqs=notch_freq, verbose="ERROR")
            except Exception:
                pass

        # Band-pass filter (0.5 to 45 Hz)
        if apply_filter:
            try:
                raw.filter(l_freq=low_cut, h_freq=high_cut, fir_design="firwin", verbose="ERROR")
            except Exception:
                pass

        # Extract annotations
        annotations = []
        if raw.annotations and len(raw.annotations) > 0:
            for annot in raw.annotations:
                desc = annot["description"].strip()
                label = ANNOTATION_LABEL_MAP.get(desc, desc.lower())
                annotations.append({
                    "onset": float(annot["onset"]),
                    "duration": float(annot["duration"]),
                    "code": desc,
                    "label": label
                })

        # Get signal data in microvolts (MNE stores in Volts by default)
        data = raw.get_data() * 1e6 # Shape: (n_channels, n_samples)
        times = raw.times # 1D timestamps (seconds)

        return {
            "file_path": edf_path,
            "sampling_rate": sfreq,
            "channel_names": clean_ch_names,
            "n_channels": len(clean_ch_names),
            "n_samples": data.shape[1],
            "duration_sec": float(raw.times[-1]) if len(raw.times) > 0 else 0.0,
            "annotations": annotations,
            "data": data,
            "times": times
        }

