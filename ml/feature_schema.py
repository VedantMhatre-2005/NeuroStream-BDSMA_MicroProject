"""
NeuroStream Feature Schema
Defines the canonical 32-dimensional feature schema for EEG Motor Imagery classification.
Ensures consistency between offline training, evaluation, and real-time streaming inference.
"""

from typing import List, Dict

TARGET_CLASSES: List[str] = ["left_hand", "right_hand", "rest"]

CLASS_TO_IDX: Dict[str, int] = {
    "left_hand": 0,
    "right_hand": 1,
    "rest": 2
}

IDX_TO_CLASS: Dict[int, str] = {v: k for k, v in CLASS_TO_IDX.items()}

FEATURE_NAMES: List[str] = [
    # Global Amplitude Statistics (6)
    "mean_amplitude",
    "std_amplitude",
    "rms_amplitude",
    "variance",
    "min_amplitude",
    "max_amplitude",
    
    # Global Band Powers - Welch PSD (5)
    "delta_power",
    "theta_power",
    "alpha_power",
    "beta_power",
    "gamma_power",
    
    # Relative Band Powers (5)
    "relative_delta",
    "relative_theta",
    "relative_alpha",
    "relative_beta",
    "relative_gamma",
    
    # Motor Cortex Channel Spectral Features (14)
    "C3_alpha_power",
    "C3_beta_power",
    "C4_alpha_power",
    "C4_beta_power",
    "Cz_alpha_power",
    "Cz_beta_power",
    "Fc3_alpha_power",
    "Fc3_beta_power",
    "Fc4_alpha_power",
    "Fc4_beta_power",
    "Cp3_alpha_power",
    "Cp3_beta_power",
    "Cp4_alpha_power",
    "Cp4_beta_power",
    
    # Lateralization Indices (2)
    "alpha_lateralization",
    "beta_lateralization"
]

FEATURE_DIM: int = len(FEATURE_NAMES) # 32

