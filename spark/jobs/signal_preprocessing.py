import numpy as np
from scipy import signal
from typing import Tuple

class SignalPreprocessor:
    """
    Signal filtering and normalization utilities for streaming EEG windows.
    """
    
    @staticmethod
    def bandpass_filter(
        data: np.ndarray,
        sfreq: int = 160,
        low_cut: float = 0.5,
        high_cut: float = 45.0,
        order: int = 4
    ) -> np.ndarray:
        """
        Applies a Butterworth bandpass filter across all EEG channels.
        data: shape (n_channels, n_samples)
        """
        nyq = 0.5 * sfreq
        low = low_cut / nyq
        high = high_cut / nyq
        
        # Ensure within bounds
        high = min(high, 0.99)
        low = max(low, 0.01)
        
        b, a = signal.butter(order, [low, high], btype="band")
        filtered = signal.filtfilt(b, a, data, axis=-1)
        return filtered

    @staticmethod
    def notch_filter(
        data: np.ndarray,
        sfreq: int = 160,
        notch_freq: float = 60.0,
        quality_factor: float = 30.0
    ) -> np.ndarray:
        """
        Removes power-line interference.
        """
        nyq = 0.5 * sfreq
        if notch_freq >= nyq:
            return data
        
        b, a = signal.iirnotch(notch_freq / nyq, quality_factor)
        filtered = signal.filtfilt(b, a, data, axis=-1)
        return filtered

    @staticmethod
    def zscore_normalize(data: np.ndarray) -> np.ndarray:
        """
        Z-score normalizes each channel independently.
        """
        means = np.mean(data, axis=-1, keepdims=True)
        stds = np.std(data, axis=-1, keepdims=True)
        stds[stds == 0] = 1.0
        return (data - means) / stds

