import os
import pytest
import numpy as np

from producer.app.eeg_loader import EEGLoader
from producer.app.window_extractor import EEGWindowExtractor
from spark.jobs.signal_preprocessing import SignalPreprocessor
from spark.jobs.feature_extraction import EEGFeatureExtractor

SAMPLE_EDF = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "S001", "S001R04.edf")

def test_signal_preprocessing():
    if not os.path.exists(SAMPLE_EDF):
        pytest.skip("Test EDF file not available.")

    rec = EEGLoader.load_recording(SAMPLE_EDF, apply_filter=False)
    data = rec["data"] # (64, n_samples)
    
    # 1. Bandpass filter
    filtered = SignalPreprocessor.bandpass_filter(data, sfreq=160, low_cut=0.5, high_cut=45.0)
    assert filtered.shape == data.shape
    assert not np.isnan(filtered).any()
    
    # 2. Z-score normalize
    normed = SignalPreprocessor.zscore_normalize(filtered)
    assert normed.shape == data.shape
    # Per-channel mean should be near 0 and std near 1
    np.testing.assert_allclose(np.mean(normed, axis=1), 0.0, atol=1e-5)
    np.testing.assert_allclose(np.std(normed, axis=1), 1.0, atol=1e-5)

def test_eeg_feature_extraction():
    if not os.path.exists(SAMPLE_EDF):
        pytest.skip("Test EDF file not available.")

    rec = EEGLoader.load_recording(SAMPLE_EDF, apply_filter=True)
    windows = EEGWindowExtractor.extract_windows(rec, "S001", "S001R04", window_duration=2.0)
    assert len(windows) > 0

    first_win = windows[0]
    win_data = np.array(first_win["data"])
    channel_names = first_win["channel_names"]

    features = EEGFeatureExtractor.extract_features(win_data, channel_names, sfreq=160)

    # Validate time-domain stats
    assert "mean_amplitude" in features
    assert "std_amplitude" in features
    assert "rms_amplitude" in features
    assert "variance" in features
    assert features["rms_amplitude"] >= 0.0
    assert features["variance"] >= 0.0

    # Validate frequency-domain band powers
    assert features["delta_power"] >= 0.0
    assert features["theta_power"] >= 0.0
    assert features["alpha_power"] >= 0.0
    assert features["beta_power"] >= 0.0
    assert features["gamma_power"] >= 0.0

    # Relative band powers should sum to 1.0
    rel_sum = (
        features["relative_delta"] +
        features["relative_theta"] +
        features["relative_alpha"] +
        features["relative_beta"] +
        features["relative_gamma"]
    )
    assert pytest.approx(rel_sum, abs=1e-2) == 1.0

    # Channel stats verification
    assert len(features["channel_stats"]) == 64
    first_ch = features["channel_stats"][0]
    assert "channel_name" in first_ch
    assert "mean" in first_ch
    assert "alpha_power" in first_ch
    assert "beta_power" in first_ch

    # Feature vector validation
    vec = features["feature_vector"]
    assert len(vec) > 20
    assert all(isinstance(x, (int, float)) and not np.isnan(x) for x in vec)

