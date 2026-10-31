import numpy as np
from scipy import signal
from typing import Dict, Any, List, Tuple

# Standard frequency band definitions in Hz
FREQ_BANDS = {
    "delta": (0.5, 4.0),
    "theta": (4.0, 8.0),
    "alpha": (8.0, 13.0),
    "beta": (13.0, 30.0),
    "gamma": (30.0, 45.0)
}

# Key sensorimotor cortex channels for motor imagery (ERD/ERS)
MOTOR_CHANNELS = ["C3", "C4", "Cz", "Fc3", "Fc4", "Cp3", "Cp4"]

class EEGFeatureExtractor:
    """
    Extracts time-domain and spectral-domain EEG features.
    Computes Welch's Power Spectral Density (PSD) and band powers.
    """

    @classmethod
    def compute_band_power(
        cls,
        freqs: np.ndarray,
        psd: np.ndarray,
        band: Tuple[float, float]
    ) -> float:
        low, high = band
        idx_band = np.logical_and(freqs >= low, freqs <= high)
        if not np.any(idx_band):
            return 0.0
        # Trapezoidal integration of PSD over the frequency range
        bp = float(np.trapz(psd[idx_band], freqs[idx_band]))
        return max(0.0, bp)

    @classmethod
    def extract_features(
        cls,
        data: np.ndarray,
        channel_names: List[str],
        sfreq: int = 160
    ) -> Dict[str, Any]:
        """
        data: numpy array of shape (n_channels, n_samples)
        """
        data = np.asarray(data, dtype=np.float64)
        n_channels, n_samples = data.shape

        # 1. Time-Domain Aggregated Statistics
        mean_amp = float(np.mean(data))
        std_amp = float(np.std(data))
        rms_amp = float(np.sqrt(np.mean(data ** 2)))
        variance = float(np.var(data))
        min_amp = float(np.min(data))
        max_amp = float(np.max(data))

        # 2. Spectral Analysis using Welch PSD
        nperseg = min(n_samples, 160)
        freqs, psd = signal.welch(
            data,
            fs=sfreq,
            nperseg=nperseg,
            noverlap=nperseg // 2,
            axis=-1
        ) # psd shape: (n_channels, n_freqs)

        # Average PSD across all channels
        avg_psd = np.mean(psd, axis=0)

        delta_power = cls.compute_band_power(freqs, avg_psd, FREQ_BANDS["delta"])
        theta_power = cls.compute_band_power(freqs, avg_psd, FREQ_BANDS["theta"])
        alpha_power = cls.compute_band_power(freqs, avg_psd, FREQ_BANDS["alpha"])
        beta_power = cls.compute_band_power(freqs, avg_psd, FREQ_BANDS["beta"])
        gamma_power = cls.compute_band_power(freqs, avg_psd, FREQ_BANDS["gamma"])

        total_power = delta_power + theta_power + alpha_power + beta_power + gamma_power
        if total_power <= 0:
            total_power = 1e-9

        rel_delta = delta_power / total_power
        rel_theta = theta_power / total_power
        rel_alpha = alpha_power / total_power
        rel_beta = beta_power / total_power
        rel_gamma = gamma_power / total_power

        # 3. Channel-Level Statistics
        channel_stats = []
        ch_alpha_powers = {}
        ch_beta_powers = {}

        for ch_idx, ch_name in enumerate(channel_names):
            ch_sig = data[ch_idx]
            ch_psd = psd[ch_idx]

            ch_mean = float(np.mean(ch_sig))
            ch_std = float(np.std(ch_sig))
            ch_rms = float(np.sqrt(np.mean(ch_sig ** 2)))
            ch_var = float(np.var(ch_sig))
            ch_min = float(np.min(ch_sig))
            ch_max = float(np.max(ch_sig))

            ch_alpha = cls.compute_band_power(freqs, ch_psd, FREQ_BANDS["alpha"])
            ch_beta = cls.compute_band_power(freqs, ch_psd, FREQ_BANDS["beta"])

            ch_alpha_powers[ch_name] = ch_alpha
            ch_beta_powers[ch_name] = ch_beta

            channel_stats.append({
                "channel_name": ch_name,
                "mean": round(ch_mean, 4),
                "std": round(ch_std, 4),
                "rms": round(ch_rms, 4),
                "variance": round(ch_var, 4),
                "min_val": round(ch_min, 4),
                "max_val": round(ch_max, 4),
                "alpha_power": round(ch_alpha, 4),
                "beta_power": round(ch_beta, 4)
            })

        # 4. Construct Feature Vector for Machine Learning
        # Global spectral & statistical features
        feature_vector = [
            mean_amp, std_amp, rms_amp, variance, min_amp, max_amp,
            delta_power, theta_power, alpha_power, beta_power, gamma_power,
            rel_delta, rel_theta, rel_alpha, rel_beta, rel_gamma
        ]

        # Sensorimotor channel specific alpha & beta features
        for mc in MOTOR_CHANNELS:
            feature_vector.append(ch_alpha_powers.get(mc, alpha_power))
            feature_vector.append(ch_beta_powers.get(mc, beta_power))

        # Mu/Beta rhythm lateralization index: (C3 - C4) / (C3 + C4)
        c3_alpha = ch_alpha_powers.get("C3", alpha_power)
        c4_alpha = ch_alpha_powers.get("C4", alpha_power)
        c3_beta = ch_beta_powers.get("C3", beta_power)
        c4_beta = ch_beta_powers.get("C4", beta_power)

        alpha_lateralization = (c3_alpha - c4_alpha) / (c3_alpha + c4_alpha + 1e-9)
        beta_lateralization = (c3_beta - c4_beta) / (c3_beta + c4_beta + 1e-9)
        feature_vector.extend([alpha_lateralization, beta_lateralization])

        return {
            "mean_amplitude": round(mean_amp, 4),
            "std_amplitude": round(std_amp, 4),
            "rms_amplitude": round(rms_amp, 4),
            "variance": round(variance, 4),
            "min_amplitude": round(min_amp, 4),
            "max_amplitude": round(max_amp, 4),
            "delta_power": round(delta_power, 4),
            "theta_power": round(theta_power, 4),
            "alpha_power": round(alpha_power, 4),
            "beta_power": round(beta_power, 4),
            "gamma_power": round(gamma_power, 4),
            "relative_delta": round(rel_delta, 4),
            "relative_theta": round(rel_theta, 4),
            "relative_alpha": round(rel_alpha, 4),
            "relative_beta": round(rel_beta, 4),
            "relative_gamma": round(rel_gamma, 4),
            "channel_stats": channel_stats,
            "feature_vector": [round(float(v), 6) for v in feature_vector]
        }

