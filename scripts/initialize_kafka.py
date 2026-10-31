#!/usr/bin/env python3
"""
Initialize Kafka Topics for NeuroStream
Creates required topics with proper partitions and replication factor.
"""

import time
import os
import sys
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError, NoBrokersAvailable

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:29092")

TOPICS = [
    {"name": "eeg.raw.windows", "num_partitions": 3, "replication_factor": 1},
    {"name": "eeg.processed.features", "num_partitions": 3, "replication_factor": 1},
    {"name": "eeg.classification.results", "num_partitions": 3, "replication_factor": 1},
    {"name": "eeg.processing.errors", "num_partitions": 1, "replication_factor": 1},
]

def initialize_topics(retries=15, delay=3):
    print(f"Connecting to Kafka at {KAFKA_BOOTSTRAP_SERVERS}...")
    admin_client = None

    for attempt in range(retries):
        try:
            admin_client = KafkaAdminClient(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                client_id="neurostream-topic-init"
            )
            print("Successfully connected to Kafka broker.")
            break
        except NoBrokersAvailable:
            print(f"Broker not available yet (attempt {attempt + 1}/{retries}). Waiting {delay}s...")
            time.sleep(delay)

    if not admin_client:
        print("Failed to connect to Kafka broker.")
        return 1

    try:
        existing_topics = admin_client.list_topics()
        print(f"Existing topics: {existing_topics}")

        new_topics = []
        for t in TOPICS:
            if t["name"] not in existing_topics:
                new_topics.append(
                    NewTopic(
                        name=t["name"],
                        num_partitions=t["num_partitions"],
                        replication_factor=t["replication_factor"]
                    )
                )

        if new_topics:
            print(f"Creating topics: {[t.name for t in new_topics]}...")
            admin_client.create_topics(new_topics=new_topics, validate_only=False)
            print("Topics created successfully.")
        else:
            print("All required topics already exist.")

        return 0
    except Exception as e:
        print(f"Error initializing topics: {e}")
        return 1
    finally:
        if admin_client:
            admin_client.close()

if __name__ == "__main__":
    sys.exit(initialize_topics())

