import os
import sys
import glob
import time
import datetime
import logging
from typing import List, Dict, Any

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from producer.app.eeg_loader import EEGLoader
from producer.app.window_extractor import EEGWindowExtractor
from spark.jobs.signal_preprocessing import SignalPreprocessor
from spark.jobs.feature_extraction import EEGFeatureExtractor
from spark.jobs.inference import StreamingInference
try:
    from backend.app.services.hdfs_service import hdfs_service
    from backend.app.integrations.hive_client import hive_client
except ModuleNotFoundError:
    from app.services.hdfs_service import hdfs_service
    from app.integrations.hive_client import hive_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("populate-hdfs-hive")

def run_population():
    logger.info("Starting HDFS & Hive data population from real PhysioNet recordings...")

    data_dir = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
    edf_files = glob.glob(os.path.join(data_dir, "*", "*.edf"))

    if not edf_files:
        logger.error(f"No EDF files found in {data_dir}. Please run scripts/download_dataset.py first.")
        return False

    logger.info(f"Discovered {len(edf_files)} EDF recordings.")

    inference_engine = StreamingInference()

    feature_records = []
    channel_stat_records = []
    prediction_records = []
    participant_aggregates = {}

    total_windows_extracted = 0

    for edf_path in edf_files:
        try:
            logger.info(f"Loading and processing {os.path.basename(edf_path)}...")
            raw = EEGLoader.load_recording(edf_path, apply_filter=True)
            fname = os.path.basename(edf_path)
            participant_id = os.path.basename(os.path.dirname(edf_path))
            recording_id = fname.replace(participant_id, "").replace(".edf", "")
            raw["participant_id"] = participant_id
            raw["recording_id"] = recording_id

            windows = EEGWindowExtractor.extract_windows(
                recording_info=raw,
                participant_id=participant_id,
                recording_id=recording_id,
                window_duration=2.0,
                window_overlap=0.5
            )

            participant_id = raw["participant_id"]
            if participant_id not in participant_aggregates:
                participant_aggregates[participant_id] = {
                    "total_windows": 0,
                    "total_left": 0,
                    "total_right": 0,
                    "total_rest": 0,
                    "alpha_powers": [],
                    "beta_powers": [],
                    "latencies": []
                }

            for win in windows:
                total_windows_extracted += 1
                data_matrix = np.array(win["data"], dtype=np.float64)
                filtered_data = SignalPreprocessor.bandpass_filter(
                    data_matrix,
                    sfreq=win["sampling_rate"],
                    low_cut=0.5,
                    high_cut=45.0
                )

                # Feature extraction
                features = EEGFeatureExtractor.extract_features(
                    filtered_data,
                    channel_names=win["channel_names"],
                    sfreq=win["sampling_rate"]
                )

                now_iso = datetime.datetime.utcnow().isoformat() + "Z"

                # 1. Feature Record
                feat_rec = {
                    "window_id": str(win["window_id"]),
                    "participant_id": str(win["participant_id"]),
                    "recording_id": str(win["recording_id"]),
                    "start_time": float(win["start_time"]),
                    "end_time": float(win["end_time"]),
                    "mean_amplitude": float(features["mean_amplitude"]),
                    "std_amplitude": float(features["std_amplitude"]),
                    "rms_amplitude": float(features["rms_amplitude"]),
                    "variance": float(features["variance"]),
                    "min_amplitude": float(features["min_amplitude"]),
                    "max_amplitude": float(features["max_amplitude"]),
                    "delta_power": float(features["delta_power"]),
                    "theta_power": float(features["theta_power"]),
                    "alpha_power": float(features["alpha_power"]),
                    "beta_power": float(features["beta_power"]),
                    "gamma_power": float(features["gamma_power"]),
                    "relative_delta": float(features["relative_delta"]),
                    "relative_theta": float(features["relative_theta"]),
                    "relative_alpha": float(features["relative_alpha"]),
                    "relative_beta": float(features["relative_beta"]),
                    "relative_gamma": float(features["relative_gamma"]),
                    "original_label": str(win["original_label"]),
                    "ingestion_timestamp": str(win["ingestion_timestamp"]),
                    "processing_timestamp": str(now_iso)
                }
                feature_records.append(feat_rec)

                # 2. Channel Statistics (for key motor/frontal channels: C3, C4, Cz, Fc3, Fc4, Cp3, Cp4, etc.)
                for ch_stat in features.get("channel_stats", []):
                    ch_name = ch_stat.get("channel_name", "")
                    if ch_name in ["C3", "C4", "Cz", "Fc3", "Fc4", "Cp3", "Cp4", "F3", "F4", "P3", "P4", "O1", "O2"]:
                        ch_rec = {
                            "window_id": str(win["window_id"]),
                            "participant_id": str(participant_id),
                            "recording_id": str(recording_id),
                            "channel_name": str(ch_name),
                            "mean": float(ch_stat["mean"]),
                            "std": float(ch_stat["std"]),
                            "rms": float(ch_stat["rms"]),
                            "variance": float(ch_stat["variance"]),
                            "min_val": float(ch_stat.get("min_val", ch_stat.get("min", 0.0))),
                            "max_val": float(ch_stat.get("max_val", ch_stat.get("max", 0.0))),
                            "alpha_power": float(ch_stat["alpha_power"]),
                            "beta_power": float(ch_stat["beta_power"]),
                            "stat_timestamp": str(now_iso)
                        }
                        channel_stat_records.append(ch_rec)

                # 3. ML Inference
                start_inf = time.time()
                pred_class, prob_map, confidence = inference_engine.predict(features["feature_vector"])
                inf_latency = round((time.time() - start_inf) * 1000.0, 2)

                pred_rec = {
                    "window_id": str(win["window_id"]),
                    "participant_id": str(win["participant_id"]),
                    "recording_id": str(win["recording_id"]),
                    "start_time": float(win["start_time"]),
                    "end_time": float(win["end_time"]),
                    "predicted_class": str(pred_class or "rest"),
                    "prob_left": float(prob_map.get("left_hand", 0.0)),
                    "prob_right": float(prob_map.get("right_hand", 0.0)),
                    "prob_rest": float(prob_map.get("rest", 0.0)),
                    "confidence": float(confidence),
                    "original_label": str(win["original_label"]),
                    "inference_latency_ms": float(inf_latency),
                    "model_version": str(inference_engine.model_metadata.get("version", "v1.0")),
                    "ingestion_timestamp": str(win["ingestion_timestamp"]),
                    "classification_timestamp": str(now_iso)
                }
                prediction_records.append(pred_rec)

                # Aggregate updates
                p_aggr = participant_aggregates[participant_id]
                p_aggr["total_windows"] += 1
                if pred_class == "left_hand":
                    p_aggr["total_left"] += 1
                elif pred_class == "right_hand":
                    p_aggr["total_right"] += 1
                else:
                    p_aggr["total_rest"] += 1
                p_aggr["alpha_powers"].append(features["alpha_power"])
                p_aggr["beta_powers"].append(features["beta_power"])
                p_aggr["latencies"].append(inf_latency)

        except Exception as e:
            logger.error(f"Error processing {edf_path}: {e}")

    logger.info(f"Processed {total_windows_extracted} total EEG windows.")
    logger.info(f"Generated {len(feature_records)} feature records, {len(channel_stat_records)} channel stats, {len(prediction_records)} predictions.")

    # 4. Construct Participant Summaries
    summary_records = []
    now_ts = datetime.datetime.utcnow().isoformat() + "Z"
    for pid, aggr in participant_aggregates.items():
        summary_records.append({
            "participant_id": str(pid),
            "total_windows": int(aggr["total_windows"]),
            "total_left_predictions": int(aggr["total_left"]),
            "total_right_predictions": int(aggr["total_right"]),
            "total_rest_predictions": int(aggr["total_rest"]),
            "avg_alpha_power": float(np.mean(aggr["alpha_powers"])) if aggr["alpha_powers"] else 0.0,
            "avg_beta_power": float(np.mean(aggr["beta_powers"])) if aggr["beta_powers"] else 0.0,
            "avg_latency_ms": float(np.mean(aggr["latencies"])) if aggr["latencies"] else 0.0,
            "last_updated": str(now_ts)
        })

    # Step 5: Write to HDFS as Parquet
    logger.info("Writing Parquet files to HDFS...")
    
    # 5.1 Features
    s1 = hdfs_service.write_parquet("/neurostream/features/eeg_features_001.parquet", feature_records)
    logger.info(f"Features write result: {s1}")

    # 5.2 Channel Statistics
    s2 = hdfs_service.write_parquet("/neurostream/channel_stats/channel_stats_001.parquet", channel_stat_records)
    logger.info(f"Channel stats write result: {s2}")

    # 5.3 Classification Results
    s3 = hdfs_service.write_parquet("/neurostream/predictions/predictions_001.parquet", prediction_records)
    logger.info(f"Predictions write result: {s3}")

    # 5.4 Participant Summary
    s4 = hdfs_service.write_parquet("/neurostream/participant_summary/summary_001.parquet", summary_records)
    logger.info(f"Participant summary write result: {s4}")

    # Step 6: Verify Hive Query Execution
    logger.info("Verifying Hive queries on newly written data...")
    overview = hive_client.get_windows_per_participant()
    logger.info(f"Hive Query 1 (Windows per participant): {overview}")

    brain_states = hive_client.get_brain_states_distribution()
    logger.info(f"Hive Query 2 (Brain states): {brain_states}")

    band_power = hive_client.get_band_power_by_state()
    logger.info(f"Hive Query 3 (Band power by state): {band_power}")

    return s1 and s2 and s3 and s4

if __name__ == "__main__":
    success = run_population()
    sys.exit(0 if success else 1)
