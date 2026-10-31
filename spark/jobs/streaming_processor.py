import os
import sys
import time
import json
import logging
import datetime
from typing import Dict, Any, List

import numpy as np
from kafka import KafkaProducer

try:
    from .signal_preprocessing import SignalPreprocessor
    from .feature_extraction import EEGFeatureExtractor
    from .inference import StreamingInference
except ImportError:
    from spark.jobs.signal_preprocessing import SignalPreprocessor
    from spark.jobs.feature_extraction import EEGFeatureExtractor
    from spark.jobs.inference import StreamingInference

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("neurostream-spark-streaming")

# Configuration
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
TOPIC_RAW = os.getenv("TOPIC_RAW_WINDOWS", "eeg.raw.windows")
TOPIC_FEATURES = os.getenv("TOPIC_PROCESSED_FEATURES", "eeg.processed.features")
TOPIC_PREDICTIONS = os.getenv("TOPIC_CLASSIFICATION_RESULTS", "eeg.classification.results")
TOPIC_ERRORS = os.getenv("TOPIC_PROCESSING_ERRORS", "eeg.processing.errors")
CHECKPOINT_DIR = os.getenv("CHECKPOINT_DIR", "/tmp/spark_checkpoints")
HDFS_URL = os.getenv("HADOOP_NAMENODE_URL", "hdfs://namenode:9000")

class SparkStreamingJob:
    def __init__(self):
        self.kafka_producer = None
        self.inference_engine = StreamingInference()
        self._init_producer()

    def _init_producer(self):
        try:
            self.kafka_producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
                acks=1
            )
            logger.info(f"Connected output Kafka producer to {KAFKA_BOOTSTRAP}")
        except Exception as e:
            logger.error(f"Error initializing Kafka output producer: {e}")

    def process_batch(self, batch_df, batch_id):
        if batch_df.isEmpty():
            return

        logger.info(f"Processing micro-batch {batch_id} with {batch_df.count()} raw EEG records.")
        rows = batch_df.collect()

        feature_records = []
        prediction_records = []

        for row in rows:
            try:
                raw_json = row["value"]
                if isinstance(raw_json, str):
                    window = json.loads(raw_json)
                else:
                    window = raw_json

                window_id = window["window_id"]
                participant_id = window["participant_id"]
                recording_id = window["recording_id"]
                start_time = window["start_time"]
                end_time = window["end_time"]
                sfreq = window.get("sampling_rate", 160)
                channel_names = window.get("channel_names", [])
                original_label = window.get("original_label", "unknown")
                ingestion_ts = window.get("ingestion_timestamp", datetime.datetime.utcnow().isoformat() + "Z")

                # EEG 2D signal data: (n_channels, n_samples)
                data = np.array(window["data"], dtype=np.float64)

                # Step 1: Preprocessing (Bandpass filter 0.5 - 45 Hz)
                filtered_data = SignalPreprocessor.bandpass_filter(data, sfreq=sfreq, low_cut=0.5, high_cut=45.0)

                # Step 2: Feature Extraction (Time domain + Welch PSD)
                features = EEGFeatureExtractor.extract_features(filtered_data, channel_names=channel_names, sfreq=sfreq)
                processing_ts = datetime.datetime.utcnow().isoformat() + "Z"

                # Construct Features Message
                feat_msg = {
                    "window_id": window_id,
                    "participant_id": participant_id,
                    "recording_id": recording_id,
                    "start_time": start_time,
                    "end_time": end_time,
                    "sampling_rate": sfreq,
                    "original_label": original_label,
                    "mean_amplitude": features["mean_amplitude"],
                    "std_amplitude": features["std_amplitude"],
                    "rms_amplitude": features["rms_amplitude"],
                    "variance": features["variance"],
                    "min_amplitude": features["min_amplitude"],
                    "max_amplitude": features["max_amplitude"],
                    "delta_power": features["delta_power"],
                    "theta_power": features["theta_power"],
                    "alpha_power": features["alpha_power"],
                    "beta_power": features["beta_power"],
                    "gamma_power": features["gamma_power"],
                    "relative_delta": features["relative_delta"],
                    "relative_theta": features["relative_theta"],
                    "relative_alpha": features["relative_alpha"],
                    "relative_beta": features["relative_beta"],
                    "relative_gamma": features["relative_gamma"],
                    "channel_stats": features["channel_stats"],
                    "feature_vector": features["feature_vector"],
                    "ingestion_timestamp": ingestion_ts,
                    "processing_timestamp": processing_ts
                }
                feature_records.append(feat_msg)

                # Step 3: Real-Time Machine Learning Inference
                inf_start = time.time()
                pred_class, prob_map, confidence = self.inference_engine.predict(features["feature_vector"])
                inf_latency = round((time.time() - inf_start) * 1000.0, 2)

                pred_msg = {
                    "window_id": window_id,
                    "participant_id": participant_id,
                    "recording_id": recording_id,
                    "start_time": start_time,
                    "end_time": end_time,
                    "predicted_class": pred_class or "model_not_trained",
                    "prob_left": prob_map.get("left_hand", 0.0),
                    "prob_right": prob_map.get("right_hand", 0.0),
                    "prob_rest": prob_map.get("rest", 0.0),
                    "confidence": confidence,
                    "original_label": original_label,
                    "inference_latency_ms": inf_latency,
                    "model_version": self.inference_engine.model_metadata.get("version", "v1.0") if pred_class else "none",
                    "ingestion_timestamp": ingestion_ts,
                    "classification_timestamp": datetime.datetime.utcnow().isoformat() + "Z"
                }
                prediction_records.append(pred_msg)

                # Publish to Kafka
                if self.kafka_producer:
                    self.kafka_producer.send(TOPIC_FEATURES, key=f"{participant_id}_{recording_id}", value=feat_msg)
                    self.kafka_producer.send(TOPIC_PREDICTIONS, key=f"{participant_id}_{recording_id}", value=pred_msg)

            except Exception as ex:
                logger.error(f"Error processing row in micro-batch {batch_id}: {ex}")
                if self.kafka_producer:
                    err_msg = {
                        "batch_id": batch_id,
                        "error": str(ex),
                        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
                    }
                    self.kafka_producer.send(TOPIC_ERRORS, value=err_msg)

        if self.kafka_producer:
            self.kafka_producer.flush()

        logger.info(f"Micro-batch {batch_id} complete: {len(feature_records)} features & {len(prediction_records)} predictions emitted.")

def run_spark_job():
    from pyspark.sql import SparkSession
    logger.info("Initializing PySpark Structured Streaming Session...")
    
    spark = SparkSession.builder \
        .appName("NeuroStream-RealTime-EEG-Streaming") \
        .config("spark.streaming.stopGracefullyOnShutdown", "true") \
        .config("spark.sql.shuffle.partitions", "2") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")
    processor = SparkStreamingJob()

    # Read stream from Kafka
    logger.info(f"Subscribing to Kafka topic: {TOPIC_RAW} from {KAFKA_BOOTSTRAP}")
    df_raw = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP) \
        .option("subscribe", TOPIC_RAW) \
        .option("startingOffsets", "latest") \
        .option("failOnDataLoss", "false") \
        .load()

    # Convert binary value to String
    df_parsed = df_raw.selectExpr("CAST(key AS STRING) as key", "CAST(value AS STRING) as value")

    # Write stream using foreachBatch
    query = df_parsed.writeStream \
        .foreachBatch(processor.process_batch) \
        .option("checkpointLocation", f"{CHECKPOINT_DIR}/spark_streaming") \
        .trigger(processingTime="1 second") \
        .start()

    logger.info("PySpark Structured Streaming query started. Awaiting termination...")
    try:
        query.awaitTermination()
    except KeyboardInterrupt:
        logger.info("Stopping PySpark Structured Streaming...")
        query.stop()

if __name__ == "__main__":
    run_spark_job()
