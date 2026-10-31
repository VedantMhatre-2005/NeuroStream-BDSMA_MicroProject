import json
import logging
import time
from typing import Dict, Any, Optional
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable, KafkaError

logger = logging.getLogger("neurostream-kafka-client")

class EEGKafkaClient:
    """
    Kafka client wrapper for reliable publishing of serialized EEG windows.
    """
    def __init__(self, bootstrap_servers: str = "localhost:29092", retries: int = 10, delay: float = 2.0):
        self.bootstrap_servers = bootstrap_servers
        self.producer: Optional[KafkaProducer] = None
        self._connect(retries, delay)

    def _connect(self, retries: int, delay: float):
        for attempt in range(retries):
            try:
                self.producer = KafkaProducer(
                    bootstrap_servers=self.bootstrap_servers,
                    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                    key_serializer=lambda k: k.encode("utf-8") if k else None,
                    acks="all",
                    retries=3,
                    linger_ms=10,
                    batch_size=32 * 1024,
                    max_request_size=5 * 1024 * 1024 # 5MB to handle 64-channel raw windows comfortably
                )
                logger.info(f"Connected to Kafka broker at {self.bootstrap_servers}")
                return
            except NoBrokersAvailable:
                logger.warning(f"Kafka broker not ready (attempt {attempt + 1}/{retries}). Retrying in {delay}s...")
                time.sleep(delay)
            except Exception as e:
                logger.error(f"Error connecting to Kafka: {e}")
                time.sleep(delay)

        raise ConnectionError(f"Could not connect to Kafka at {self.bootstrap_servers} after {retries} attempts.")

    def publish_window(self, topic: str, window: Dict[str, Any]) -> bool:
        if not self.producer:
            raise RuntimeError("Kafka producer is not connected.")
        
        try:
            key = f"{window.get('participant_id', 'unknown')}_{window.get('recording_id', 'unknown')}"
            future = self.producer.send(topic, key=key, value=window)
            # We don't block on every message for streaming throughput, but log errors
            return True
        except KafkaError as e:
            logger.error(f"Failed to publish window {window.get('window_id')}: {e}")
            return False

    def flush(self):
        if self.producer:
            self.producer.flush()

    def close(self):
        if self.producer:
            self.producer.flush()
            self.producer.close()

