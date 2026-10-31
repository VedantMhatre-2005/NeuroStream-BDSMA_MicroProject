import os
import sys
import json
import time

from producer.app.eeg_loader import EEGLoader
from producer.app.window_extractor import EEGWindowExtractor
from producer.app.kafka_client import EEGKafkaClient
from spark.jobs.streaming_processor import SparkStreamingJob
from kafka import KafkaConsumer

def test_pipeline():
    print("=" * 60)
    print(" Testing End-to-End Streaming & Feature Processing")
    print("=" * 60)

    # 1. Load real EDF and extract 5 windows
    sample_edf = "/app/data/raw/S001/S001R04.edf"
    print(f"Loading {sample_edf}...")
    rec = EEGLoader.load_recording(sample_edf, apply_filter=True)
    windows = EEGWindowExtractor.extract_windows(rec, "S001", "S001R04", window_duration=2.0)[:5]
    print(f"Extracted {len(windows)} test windows.")

    # 2. Publish to eeg.raw.windows
    kafka_client = EEGKafkaClient(bootstrap_servers="kafka:9092")
    for w in windows:
        kafka_client.publish_window("eeg.raw.windows", w)
    kafka_client.flush()
    print("Published 5 test windows to eeg.raw.windows.")

    # 3. Process via SparkStreamingJob processor
    processor = SparkStreamingJob()
    
    # Mock row structure to test batch processing
    class MockRow(dict):
        pass

    mock_rows = [MockRow({"value": json.dumps(w)}) for w in windows]
    
    class MockDF:
        def isEmpty(self):
            return False
        def count(self):
            return len(mock_rows)
        def collect(self):
            return mock_rows

    print("Executing SparkStreamingJob.process_batch...")
    processor.process_batch(MockDF(), batch_id=1)

    # 4. Consume from eeg.processed.features
    print("Verifying published features in eeg.processed.features...")
    consumer = KafkaConsumer(
        "eeg.processed.features",
        bootstrap_servers="kafka:9092",
        auto_offset_reset="latest",
        enable_auto_commit=False,
        consumer_timeout_ms=5000,
        value_deserializer=lambda m: json.loads(m.decode("utf-8"))
    )

    # Also check from beginning if needed
    consumer_early = KafkaConsumer(
        "eeg.processed.features",
        bootstrap_servers="kafka:9092",
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        consumer_timeout_ms=5000,
        value_deserializer=lambda m: json.loads(m.decode("utf-8"))
    )
    
    messages = []
    for msg in consumer_early:
        messages.append(msg.value)
        if len(messages) >= 1:
            break

    assert len(messages) > 0, "No messages received in eeg.processed.features!"
    feat = messages[0]
    print(f"Successfully consumed processed feature message for window: {feat['window_id']}")
    print(f"  Alpha power: {feat['alpha_power']:.4f}")
    print(f"  Beta power:  {feat['beta_power']:.4f}")
    print(f"  Channels:    {len(feat['channel_stats'])}")
    print(f"  Feature Vec: {len(feat['feature_vector'])} dims")

    consumer_early.close()
    print("=" * 60)
    print("Pipeline validation PASSED successfully!")
    print("=" * 60)

if __name__ == "__main__":
    test_pipeline()

