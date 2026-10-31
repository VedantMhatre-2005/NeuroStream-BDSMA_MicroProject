import os
import sys
import time
import json
import logging
import threading
import datetime
from typing import Optional, Dict, Any, List
import numpy as np

from .eeg_loader import EEGLoader
from .window_extractor import EEGWindowExtractor
from .kafka_client import EEGKafkaClient
from spark.jobs.signal_preprocessing import SignalPreprocessor
from spark.jobs.feature_extraction import EEGFeatureExtractor
from spark.jobs.inference import StreamingInference

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("neurostream-producer")

class EEGStreamingProducer:
    """
    Manages streaming of real EEG windows into Apache Kafka.
    Supports continuous looping playback, pause, resume, stop, speed multipliers, and real-time ML inference.
    """
    def __init__(
        self,
        bootstrap_servers: str = None,
        raw_topic: str = "eeg.raw.windows",
        data_dir: str = None
    ):
        self.bootstrap_servers = bootstrap_servers or os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:29092")
        self.raw_topic = raw_topic or os.getenv("TOPIC_RAW_WINDOWS", "eeg.raw.windows")
        self.predictions_topic = os.getenv("TOPIC_CLASSIFICATION_RESULTS", "eeg.classification.results")
        self.features_topic = os.getenv("TOPIC_PROCESSED_FEATURES", "eeg.processed.features")
        self.data_dir = data_dir or os.getenv("DATA_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "raw"))
        
        self.kafka_client: Optional[EEGKafkaClient] = None
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        
        # Inference Engine & Callbacks
        self.inference_engine = StreamingInference()
        self.on_prediction_callback = None
        self.recent_predictions: List[Dict[str, Any]] = []

        # State & Telemetry
        self.state = "stopped"  # "stopped", "running", "paused"
        self.loop = True
        self.current_participant: Optional[str] = None
        self.current_recording: Optional[str] = None
        self.replay_speed: float = float(os.getenv("REPLAY_SPEED", 1.0))
        self.window_duration: float = float(os.getenv("WINDOW_DURATION", 2.0))
        self.window_overlap: float = float(os.getenv("WINDOW_OVERLAP", 0.5))
        
        self.total_windows_published: int = 0
        self.current_window_idx: int = 0
        self.total_windows_in_recording: int = 0
        self.last_published_window_id: Optional[str] = None
        self.last_published_time: Optional[float] = None
        self.start_timestamp: Optional[float] = None
        self.throughput: float = 0.0

    def _ensure_kafka_connected(self):
        if not self.kafka_client:
            self.kafka_client = EEGKafkaClient(bootstrap_servers=self.bootstrap_servers)

    def set_replay_speed(self, speed: float):
        self.replay_speed = max(0.1, float(speed))
        logger.info(f"Replay speed updated to {self.replay_speed}x")

    def get_status(self) -> Dict[str, Any]:
        elapsed = (time.time() - self.start_timestamp) if (self.start_timestamp and self.state == "running") else 0.0
        return {
            "state": self.state,
            "participant_id": self.current_participant,
            "recording_id": self.current_recording,
            "replay_speed": self.replay_speed,
            "loop": self.loop,
            "window_duration": self.window_duration,
            "window_overlap": self.window_overlap,
            "windows_published": self.total_windows_published,
            "current_window_idx": self.current_window_idx,
            "total_windows_in_recording": self.total_windows_in_recording,
            "last_window_id": self.last_published_window_id,
            "throughput_wps": round(self.throughput, 2),
            "elapsed_seconds": round(elapsed, 2)
        }

    def start_streaming(
        self,
        participant_id: str = "S001",
        recording_id: str = "S001R04",
        replay_speed: float = 1.0,
        from_beginning: bool = False,
        loop: bool = True
    ):
        if self.state == "running":
            logger.warning("Streaming is already running.")
            return

        self._ensure_kafka_connected()

        # Reset window index if switching recording
        if self.current_recording != recording_id:
            self.current_window_idx = 0
            self.total_windows_published = 0

        self.current_participant = participant_id
        self.current_recording = recording_id
        self.replay_speed = max(0.1, replay_speed)
        self.loop = loop
        
        self._stop_event.clear()
        self._pause_event.clear()
        
        if from_beginning or (self.total_windows_in_recording > 0 and self.current_window_idx >= self.total_windows_in_recording):
            self.current_window_idx = 0

        self.state = "running"
        self.start_timestamp = time.time()
        
        self._thread = threading.Thread(
            target=self._stream_worker,
            args=(participant_id, recording_id),
            daemon=True
        )
        self._thread.start()
        logger.info(f"Started continuous streaming {recording_id} (participant {participant_id}) at {self.replay_speed}x speed (loop={self.loop}).")

    def pause_streaming(self):
        if self.state == "running":
            self._pause_event.set()
            self.state = "paused"
            logger.info("Streaming paused.")

    def resume_streaming(self):
        if self.state == "paused":
            self._pause_event.clear()
            self.state = "running"
            logger.info("Streaming resumed.")

    def stop_streaming(self):
        self._stop_event.set()
        self._pause_event.clear()
        self.state = "stopped"
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        logger.info("Streaming stopped.")

    def _stream_worker(self, participant_id: str, recording_id: str):
        edf_filename = f"{recording_id}.edf"
        edf_path = os.path.join(self.data_dir, participant_id, edf_filename)
        
        if not os.path.exists(edf_path):
            alt_path = os.path.join(self.data_dir, edf_filename)
            if os.path.exists(alt_path):
                edf_path = alt_path
            else:
                logger.error(f"Recording file not found: {edf_path}")
                self.state = "error"
                return

        logger.info(f"Loading EEG file for streaming: {edf_path}")
        recording_info = EEGLoader.load_recording(
            edf_path=edf_path,
            apply_filter=True,
            low_cut=0.5,
            high_cut=45.0
        )
        
        windows = EEGWindowExtractor.extract_windows(
            recording_info=recording_info,
            participant_id=participant_id,
            recording_id=recording_id,
            window_duration=self.window_duration,
            window_overlap=self.window_overlap
        )
        
        self.total_windows_in_recording = len(windows)
        logger.info(f"Loaded {len(windows)} windows for streaming.")

        step_seconds = self.window_duration * (1.0 - self.window_overlap)
        start_time = time.time()
        count = 0

        while not self._stop_event.is_set():
            if self.current_window_idx >= len(windows):
                self.current_window_idx = 0

            base_sleep = max(0.05, step_seconds / max(0.1, self.replay_speed))

            for idx in range(self.current_window_idx, len(windows)):
                if self._stop_event.is_set():
                    break

                # Handle pause
                while self._pause_event.is_set() and not self._stop_event.is_set():
                    time.sleep(0.1)

                if self._stop_event.is_set():
                    break

                window = windows[idx]
                
                # 1. Publish Raw Window to Kafka
                self.kafka_client.publish_window(self.raw_topic, window)
                
                # 2. Extract Features & Run Inference in Streaming Loop
                try:
                    data_matrix = np.array(window["data"], dtype=np.float64)
                    sfreq = window.get("sampling_rate", 160)
                    filtered = SignalPreprocessor.bandpass_filter(data_matrix, sfreq=sfreq, low_cut=0.5, high_cut=45.0)
                    features = EEGFeatureExtractor.extract_features(
                        filtered,
                        channel_names=window.get("channel_names", []),
                        sfreq=sfreq
                    )

                    inf_start = time.time()
                    pred_class, prob_map, confidence = self.inference_engine.predict(features["feature_vector"])
                    inf_latency = round((time.time() - inf_start) * 1000.0, 2)

                    now_iso = datetime.datetime.utcnow().isoformat() + "Z"
                    pred_msg = {
                        "window_id": window["window_id"],
                        "participant_id": participant_id,
                        "recording_id": recording_id,
                        "start_time": round(float(window["start_time"]), 2),
                        "end_time": round(float(window["end_time"]), 2),
                        "predicted_class": str(pred_class or "rest"),
                        "prob_left": round(float(prob_map.get("left_hand", 0.0)), 4),
                        "prob_right": round(float(prob_map.get("right_hand", 0.0)), 4),
                        "prob_rest": round(float(prob_map.get("rest", 0.0)), 4),
                        "confidence": round(float(confidence), 4),
                        "original_label": str(window.get("original_label", "rest")),
                        "inference_latency_ms": inf_latency,
                        "model_version": "v1.0",
                        "ingestion_timestamp": window.get("ingestion_timestamp", now_iso),
                        "classification_timestamp": now_iso
                    }

                    # 3. Publish Prediction to Kafka
                    self.kafka_client.publish_window(self.predictions_topic, pred_msg)

                    # 4. Cache in recent predictions ring buffer
                    self.recent_predictions.insert(0, pred_msg)
                    if len(self.recent_predictions) > 50:
                        self.recent_predictions.pop()

                    # 5. Broadcast to WebSocket callback if registered
                    if self.on_prediction_callback:
                        try:
                            self.on_prediction_callback(pred_msg)
                        except Exception as cb_err:
                            logger.error(f"Error in prediction callback: {cb_err}")

                except Exception as inf_err:
                    logger.error(f"Error running inference during streaming: {inf_err}")

                self.total_windows_published += 1
                self.current_window_idx = idx + 1
                self.last_published_window_id = window["window_id"]
                self.last_published_time = time.time()
                count += 1

                # Calculate throughput
                elapsed = time.time() - start_time
                if elapsed > 0:
                    self.throughput = count / elapsed

                if idx % 15 == 0:
                    logger.info(f"Published window {idx + 1}/{len(windows)} [{window['original_label']}] - Rate: {self.throughput:.1f} w/s")

                # Sleep according to replay speed (re-evaluating speed dynamically)
                base_sleep = max(0.05, step_seconds / max(0.1, self.replay_speed))
                time.sleep(base_sleep)

            # Check if continuous looping is enabled
            if not self.loop or self._stop_event.is_set():
                break

            logger.info(f"Reached end of recording {recording_id} ({len(windows)} windows). Looping from beginning...")
            self.current_window_idx = 0

        self.kafka_client.flush()
        if not self._stop_event.is_set():
            logger.info(f"Completed streaming for {recording_id}.")
        self.state = "stopped"

if __name__ == "__main__":
    producer = EEGStreamingProducer()
    producer.start_streaming("S001", "S001R04", replay_speed=2.0)
    try:
        while producer.state == "running":
            time.sleep(1)
    except KeyboardInterrupt:
        producer.stop_streaming()
