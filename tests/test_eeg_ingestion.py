import os
import json
import pytest
import numpy as np

from producer.app.eeg_loader import EEGLoader
from producer.app.window_extractor import EEGWindowExtractor

SAMPLE_EDF = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "S001", "S001R04.edf")

def test_edf_loader_real_data():
    if not os.path.exists(SAMPLE_EDF):
        pytest.skip("Test EDF file not downloaded yet.")

    recording = EEGLoader.load_recording(SAMPLE_EDF, apply_filter=True)
    
    assert recording["sampling_rate"] == 160
    assert recording["n_channels"] == 64
    assert recording["n_samples"] > 1600 # At least 10 seconds of data
    assert recording["duration_sec"] > 10.0
    assert len(recording["annotations"]) > 0
    
    labels = {a["label"] for a in recording["annotations"]}
    assert any(lbl in ["rest", "left_hand", "right_hand"] for lbl in labels)

def test_window_extractor():
    if not os.path.exists(SAMPLE_EDF):
        pytest.skip("Test EDF file not downloaded yet.")

    recording = EEGLoader.load_recording(SAMPLE_EDF, apply_filter=True)
    windows = EEGWindowExtractor.extract_windows(
        recording_info=recording,
        participant_id="S001",
        recording_id="S001R04",
        window_duration=2.0,
        window_overlap=0.5
    )

    assert len(windows) > 0
    first_w = windows[0]
    
    # Dimension verification
    assert first_w["sampling_rate"] == 160
    assert first_w["n_channels"] == 64
    assert first_w["n_samples"] == 320
    assert len(first_w["data"]) == 64
    assert len(first_w["data"][0]) == 320
    
    # Metadata verification
    assert first_w["participant_id"] == "S001"
    assert first_w["recording_id"] == "S001R04"
    assert "window_id" in first_w
    assert first_w["original_label"] in ["rest", "left_hand", "right_hand"]
    assert first_w["start_time"] == 0.0
    assert first_w["end_time"] == 2.0

def test_window_json_serialization():
    if not os.path.exists(SAMPLE_EDF):
        pytest.skip("Test EDF file not downloaded yet.")

    recording = EEGLoader.load_recording(SAMPLE_EDF, apply_filter=True)
    windows = EEGWindowExtractor.extract_windows(
        recording_info=recording,
        participant_id="S001",
        recording_id="S001R04",
        window_duration=2.0,
        window_overlap=0.5
    )
    
    w = windows[0]
    serialized = json.dumps(w)
    assert isinstance(serialized, str)
    deserialized = json.loads(serialized)
    
    assert deserialized["window_id"] == w["window_id"]
    assert len(deserialized["data"]) == 64
    assert len(deserialized["data"][0]) == 320

