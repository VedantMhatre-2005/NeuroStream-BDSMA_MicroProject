# NeuroStream Operational Cookbook & Engineering Manual

> **System:** NeuroStream — Real-Time EEG Brain-State Classification and Big Data Analytics  
> **Target Audience:** Distributed Systems Engineers, Big Data Architects, Data Scientists, and Researchers  
> **Environment:** Docker Engine / Docker Compose (WSL2 / Linux / macOS), Python 3.11+, Java 11/17 (containerized)

---

## Table of Contents

1. [Architecture & System Topography](#1-architecture--system-topography)
2. [Prerequisites & Environment Configuration](#2-prerequisites--environment-configuration)
3. [Infrastructure Provisioning Recipe](#3-infrastructure-provisioning-recipe)
4. [Dataset Acquisition Recipe](#4-dataset-acquisition-recipe)
5. [Machine Learning Training & Evaluation Recipe](#5-machine-learning-training--evaluation-recipe)
6. [HDFS Parquet Lake & Hive Population Recipe](#6-hdfs-parquet-lake--hive-population-recipe)
7. [Real-Time Streaming Pipeline Execution Recipe](#7-real-time-streaming-pipeline-execution-recipe)
8. [FastAPI REST & WebSocket Consumption Recipes](#8-fastapi-rest--websocket-consumption-recipes)
9. [Apache Hive Interactive SQL Analytics Recipes](#9-apache-hive-interactive-sql-analytics-recipes)
10. [Automated Testing & Quality Assurance Recipe](#10-automated-testing--quality-assurance-recipe)
11. [Operational Troubleshooting & Diagnostic Runbook](#11-operational-troubleshooting--diagnostic-runbook)
12. [Teardown, Maintenance & Data Management Recipe](#12-teardown-maintenance--data-management-recipe)

---

## 1. Architecture & System Topography

NeuroStream processes human brainwaves in real-time across a distributed pipeline:

```
[PhysioNet EEGMMIDB (.edf)]
         |
         v
[Python EEG Producer] ---> [Kafka 3.7.0 (KRaft)]
                                  |
                                  v
                    [Spark 3.5.1 Structured Streaming]
                                  |
                    +-------------+-------------+
                    |                           |
                    v                           v
         [eeg.processed.features]    [eeg.classification.results]
                    |                           |
                    +-------------+-------------+
                                  |
                                  v
                    [Hadoop 3.3.6 HDFS Parquet Lake]
                                  |
                                  v
                    [Apache Hive 4.0.0 HiveServer2]
                                  |
                    [FastAPI REST + WebSocket Gateway]
                                  |
                    [React 18 + Vite Web Dashboard]
```

### Pinned Network Endpoints

| Container / Service | Port (Host / Bridge) | Protocol / URI | Description |
|---|---|---|---|
| `postgres` | `5432:5432` | TCP / PostgreSQL | Hive Metastore persistence |
| `kafka` | `9092:9092`, `29092:29092` | PLAINTEXT | Ingestion and inference message broker |
| `namenode` | `9870:9870`, `9000:9000` | HTTP / HDFS RPC | Hadoop HDFS Master Web UI & RPC |
| `datanode` | `9864:9864` | HTTP / Data transfer | Hadoop HDFS Block Storage |
| `hive-metastore` | `9083:9083` | Thrift | Hive Metastore catalog service |
| `hive-server` | `10000:10000`, `10002:10002` | Thrift / HTTP | HiveServer2 JDBC/ODBC and Web UI |
| `spark-master` | `8080:8080`, `7077:7077` | HTTP / Spark RPC | Spark Master Web UI & Cluster Dispatcher |
| `spark-worker` | `8081:8081` | HTTP | Spark Worker Web UI |
| `neurostream-backend` | `8000:8000` | HTTP / WS | FastAPI Gateway, OpenAPI Docs, WebSocket `/ws/live` |
| `neurostream-frontend` | `3000:3000` | HTTP | React 18 Single Page Application |

---

## 2. Prerequisites & Environment Configuration

### Resource Sizing Guidelines
- **CPU:** 4 physical cores minimum (8 vCPUs recommended).
- **RAM:** Minimum 8 GB assigned to Docker daemon (12 GB–16 GB recommended).
- **Disk:** 20 GB free disk space for raw recordings, Docker layers, Parquet blocks, and HDFS metadata.

### Configuration Recipe (`.env`)

1. Copy the template:
   ```bash
   cp .env.example .env
   # On Windows PowerShell:
   Copy-Item .env.example .env
   ```

2. Confirm the operational variables in `.env`:
   ```ini
   # Kafka
   KAFKA_BOOTSTRAP_SERVERS=kafka:9092
   TOPIC_RAW_WINDOWS=eeg.raw.windows
   TOPIC_PROCESSED_FEATURES=eeg.processed.features
   TOPIC_CLASSIFICATION_RESULTS=eeg.classification.results
   TOPIC_PROCESSING_ERRORS=eeg.processing.errors

   # Hadoop HDFS
   HADOOP_NAMENODE_URL=hdfs://namenode:9000

   # Hive
   HIVE_HOST=hive-server
   HIVE_PORT=10000
   HIVE_DATABASE=neurostream_db

   # Spark
   SPARK_MASTER=spark://spark-master:7077

   # Signal Ingestion Parameters
   WINDOW_DURATION=2.0
   WINDOW_OVERLAP=0.5
   SAMPLING_RATE=160
   REPLAY_SPEED=1.0
   ```

---

## 3. Infrastructure Provisioning Recipe

### Launch All Containers

```bash
docker compose up -d --build
```

### Inspect Container Health

```bash
docker compose ps
```

### Health Check Script

Run the built-in socket health check from within the backend container:

```bash
docker exec neurostream-backend python scripts/health_check.py
```

Expected output:
```
[INFO] Checking Kafka on kafka:9092 ... OK
[INFO] Checking NameNode on namenode:9000 ... OK
[INFO] Checking HiveServer2 on hive-server:10000 ... OK
[INFO] Checking Spark Master on spark-master:7077 ... OK
[INFO] All critical infrastructure nodes are operational.
```

---

## 4. Dataset Acquisition Recipe

NeuroStream streams data from the **PhysioNet EEG Motor Movement/Imagery Dataset (EEGMMIDB)**.

### Target Experimental Runs

- **Run 04 (R04):** Left vs Right fist motor imagery (Task 1).
- **Run 08 (R08):** Left vs Right fist motor imagery (Task 1 repetition).
- **Run 12 (R12):** Left vs Right fist motor imagery (Task 1 repetition).
- **Subjects:** `S001`, `S002`, `S003` (9 runs total, ~1,110 two-second EEG windows).

### Execution Command

```bash
docker exec neurostream-backend python scripts/download_dataset.py
```

### Verification
Check downloaded EDF files and directory manifest:
```bash
docker exec neurostream-backend ls -lh /app/data/raw/S001
docker exec neurostream-backend ls -lh /app/data/raw/manifest.json
```

Or query the REST API:
```bash
curl -s http://localhost:8000/api/dataset/status | jq .
```

---

## 5. Machine Learning Training & Evaluation Recipe

The ML pipeline performs:
1. Signal segmenting into 2.0-second sliding windows (50% overlap).
2. 0.5–45 Hz bandpass filtering.
3. Feature extraction (32-D vector: 6 statistical moments, 5 Welch PSD bands, 5 relative powers, 14 motor channel powers over C3/C4/Cz/Fc3/Fc4/Cp3/Cp4, and 2 lateralization indices).
4. Stratified train/test split (75% train, 25% test).
5. Fits a 100-tree balanced `RandomForestClassifier`.

### Execution Command

```bash
docker exec neurostream-backend python ml/train.py
```

### Programmatic Evaluation & Metrics Check

Inspect the saved model artifact and evaluation metadata:
```bash
docker exec neurostream-backend python -c "
import json
with open('/app/data/models/model_metadata.json') as f:
    meta = json.load(f)
print('Accuracy:', meta.get('metrics', {}).get('accuracy'))
print('Classes:', meta.get('classes'))
print('Top Features:', list(meta.get('feature_importances', {}).keys())[:5])
"
```

Or query via REST API:
```bash
curl -s http://localhost:8000/api/model/status | jq .
curl -s http://localhost:8000/api/model/evaluation | jq .
```

---

## 6. HDFS Parquet Lake & Hive Population Recipe

To enable immediate Hive SQL analytics without waiting for hours of continuous real-time streaming, run the batch population script.

### What This Recipe Does
1. Parses all 9 downloaded PhysioNet recordings.
2. Extracts 1,110+ windows and computes 32-D features.
3. Generates real-time model inferences with prediction probabilities.
4. Serializes records into Apache Parquet format (Snappy compression).
5. Uploads files into HDFS paths:
   - `/neurostream/features/`
   - `/neurostream/channel_stats/`
   - `/neurostream/predictions/`
   - `/neurostream/participant_summary/`
6. Verifies Hive external table mapping.

### Execution Command

```bash
docker exec neurostream-backend python scripts/populate_hdfs_hive.py
```

### Verify HDFS Directory Structure

```bash
docker exec namenode hdfs dfs -ls -R /neurostream
```

Expected structure:
```
drwxr-xr-x   - root supergroup          0 /neurostream/channel_stats
-rw-r--r--   1 root supergroup     ...   /neurostream/channel_stats/channel_stats_001.parquet
drwxr-xr-x   - root supergroup          0 /neurostream/features
-rw-r--r--   1 root supergroup     ...   /neurostream/features/eeg_features_001.parquet
drwxr-xr-x   - root supergroup          0 /neurostream/participant_summary
-rw-r--r--   1 root supergroup     ...   /neurostream/participant_summary/summary_001.parquet
drwxr-xr-x   - root supergroup          0 /neurostream/predictions
-rw-r--r--   1 root supergroup     ...   /neurostream/predictions/predictions_001.parquet
```

---

## 7. Real-Time Streaming Pipeline Execution Recipe

This recipe runs live streaming from Kafka through Spark and the WebSocket interface.

### Step 1: Initialize Kafka Topics

```bash
docker exec neurostream-backend python scripts/initialize_kafka.py
```

Verify topics in Kafka:
```bash
docker exec kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list
```

### Step 2: Launch Spark Structured Streaming Job

Submit the streaming processor to the Spark Master:

```bash
docker exec -d neurostream-backend python spark/jobs/streaming_processor.py
```

View the live Spark streaming job in your browser at `http://localhost:8080`.

### Step 3: Trigger Live EEG Ingestion Replay

Start the background producer streaming participant `S001` run `S001R04` at 1.0x replay speed:

```bash
curl -X POST http://localhost:8000/api/streaming/start \
  -H "Content-Type: application/json" \
  -d '{"participant_id": "S001", "recording_id": "S001R04", "replay_speed": 1.0, "loop": true}'
```

Check streaming status:
```bash
curl -s http://localhost:8000/api/streaming/status | jq .
```

Adjust replay speed dynamically:
```bash
# Accelerate to 2.5x speed
curl -X POST http://localhost:8000/api/streaming/speed \
  -H "Content-Type: application/json" \
  -d '{"speed": 2.5}'
```

Pause or Stop:
```bash
curl -X POST http://localhost:8000/api/streaming/pause
curl -X POST http://localhost:8000/api/streaming/resume
curl -X POST http://localhost:8000/api/streaming/stop
```

---

## 8. FastAPI REST & WebSocket Consumption Recipes

### Live WebSocket Stream (`/ws/live`)

The backend broadcasts real-time prediction events emitted by the streaming engine over WebSockets.

#### JavaScript / Frontend Client Example:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/live');

ws.onopen = () => console.log('Connected to NeuroStream live feed');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Window ID:', data.window_id);
  console.log('Brain State:', data.predicted_class, 'Confidence:', data.confidence);
  console.log('Probabilities: Left:', data.prob_left, 'Right:', data.prob_right, 'Rest:', data.prob_rest);
};

ws.onerror = (err) => console.error('WebSocket Error:', err);
ws.onclose = () => console.log('WebSocket closed');
```

#### Python Client Example:
```python
import asyncio
import websockets
import json

async def stream_live():
    uri = "ws://localhost:8000/ws/live"
    async with websockets.connect(uri) as websocket:
        print("Connected to NeuroStream WebSocket.")
        while True:
            msg = await websocket.recv()
            data = json.loads(msg)
            print(f"[{data.get('recording_id')}] Predicted: {data.get('predicted_class')} ({data.get('confidence')*100:.1f}%)")

asyncio.run(stream_live())
```

### Essential REST Endpoints Reference

```bash
# 1. System health and component status
curl -s http://localhost:8000/api/system/status | jq .

# 2. Host CPU/Memory/Disk resource telemetry
curl -s http://localhost:8000/api/system/resources | jq .

# 3. Analytics overview (Hive-backed)
curl -s http://localhost:8000/api/analytics/overview | jq .

# 4. Brain state distribution
curl -s http://localhost:8000/api/analytics/brain-states | jq .

# 5. List available Hive tables
curl -s http://localhost:8000/api/hive/tables | jq .

# 6. Retrieve schema for eeg_window_features
curl -s http://localhost:8000/api/hive/schema/eeg_window_features | jq .
```

---

## 9. Apache Hive Interactive SQL Analytics Recipes

HiveServer2 runs on port 10000. You can query it via the FastAPI endpoint `/api/hive/query` or via Beeline CLI inside the container.

### Recipe: Querying via Beeline CLI

```bash
docker exec -it hive-server beeline -u "jdbc:hive2://localhost:10000/neurostream_db" -n hive -p hivepassword -e "
SELECT predicted_class, COUNT(*) AS count, ROUND(AVG(confidence), 3) AS avg_conf
FROM eeg_classification_results
GROUP BY predicted_class;
"
```

### Recipe: Querying via REST API

```bash
curl -X POST http://localhost:8000/api/hive/query \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT participant_id, COUNT(*) AS total_windows FROM eeg_window_features GROUP BY participant_id"}' | jq .
```

### The 8 Canonical Analytic Queries

#### 1. Ingestion Volume by Participant
```sql
SELECT participant_id, COUNT(*) AS total_windows
FROM eeg_window_features
GROUP BY participant_id
ORDER BY total_windows DESC;
```

#### 2. Predicted Brain-State Distribution & Average Confidence
```sql
SELECT predicted_class, COUNT(*) AS count, ROUND(AVG(confidence), 4) AS avg_confidence
FROM eeg_classification_results
GROUP BY predicted_class;
```

#### 3. Spectral Band Powers by Brain State
```sql
SELECT c.predicted_class,
       ROUND(AVG(f.delta_power), 2) AS avg_delta,
       ROUND(AVG(f.alpha_power), 2) AS avg_alpha,
       ROUND(AVG(f.beta_power), 2) AS avg_beta
FROM eeg_window_features f
JOIN eeg_classification_results c ON f.window_id = c.window_id
GROUP BY c.predicted_class;
```

#### 4. Top Active Channels by Beta Activity (Motor Cortex Dynamics)
```sql
SELECT channel_name, ROUND(AVG(variance), 2) AS avg_variance, ROUND(AVG(beta_power), 2) AS avg_beta
FROM eeg_channel_statistics
GROUP BY channel_name
ORDER BY avg_beta DESC LIMIT 20;
```

#### 5. Subject-Level Prediction Matrix
```sql
SELECT participant_id, predicted_class, COUNT(*) AS prediction_count
FROM eeg_classification_results
GROUP BY participant_id, predicted_class;
```

#### 6. Beta/Alpha Power Ratio by Physical Task Label
```sql
SELECT original_label, ROUND(AVG(beta_power / NULLIF(alpha_power, 0)), 3) AS beta_alpha_ratio
FROM eeg_window_features
GROUP BY original_label;
```

#### 7. Temporal Prediction Rate and Inference Latency
```sql
SELECT SUBSTR(classification_timestamp, 1, 16) AS time_minute,
       COUNT(*) AS predictions_per_minute,
       ROUND(AVG(inference_latency_ms), 2) AS avg_latency_ms
FROM eeg_classification_results
GROUP BY SUBSTR(classification_timestamp, 1, 16)
ORDER BY time_minute DESC LIMIT 30;
```

#### 8. Granular Brain State Breakdown by Recording Run
```sql
SELECT recording_id, COUNT(*) AS total_predictions,
       SUM(CASE WHEN predicted_class = 'left_hand' THEN 1 ELSE 0 END) AS left_hand_count,
       SUM(CASE WHEN predicted_class = 'right_hand' THEN 1 ELSE 0 END) AS right_hand_count,
       SUM(CASE WHEN predicted_class = 'rest' THEN 1 ELSE 0 END) AS rest_count
FROM eeg_classification_results
GROUP BY recording_id;
```

---

## 10. Automated Testing & Quality Assurance Recipe

The project includes unit, integration, and end-to-end test suites located in `tests/`.

### Run All Tests

```bash
docker exec neurostream-backend pytest tests/ -v
```

### Run Tests by Functional Domain

```bash
# 1. Feature Extraction & DSP Logic
docker exec neurostream-backend pytest tests/test_feature_extraction.py -v

# 2. Machine Learning Model Training & Scoring
docker exec neurostream-backend pytest tests/test_ml.py -v

# 3. EEG Ingestion & Window Extractor
docker exec neurostream-backend pytest tests/test_eeg_ingestion.py -v

# 4. HDFS & Hive Connectivity
docker exec neurostream-backend pytest tests/test_hdfs_hive.py -v

# 5. FastAPI Endpoints
docker exec neurostream-backend pytest tests/test_api.py -v

# 6. Complete End-to-End Suite
docker exec neurostream-backend pytest tests/test_end_to_end.py -v
```

---

## 11. Operational Troubleshooting & Diagnostic Runbook

### Issue A: Port Conflict on Host (e.g. Port 5432 or 8080 already in use)
**Symptom:** `Error response from daemon: Ports are not available: exposing port TCP 0.0.0.0:5432`  
**Resolution:**
1. Identify the process holding the port on your host:
   - On Windows: `netstat -ano | findstr :5432`
   - On Linux/macOS: `sudo lsof -i :5432`
2. Stop the local service (e.g. a local PostgreSQL or Tomcat instance), or re-map the port in `docker-compose.yml` (e.g., `"5433:5432"`).

### Issue B: HDFS NameNode in SafeMode
**Symptom:** `org.apache.hadoop.hdfs.server.namenode.SafeModeException: Cannot create file. Name node is in safe mode.`  
**Cause:** NameNode enters SafeMode on startup while awaiting DataNode block reports.  
**Resolution:** Force NameNode to leave SafeMode manually:
```bash
docker exec namenode hdfs dfsadmin -safemode leave
```

### Issue C: Hive Metastore or HiveServer2 Connection Refused
**Symptom:** `Connection refused to hive-server:10000` or PyHive/Thrift error.  
**Cause:** PostgreSQL metastore database not ready or schema not yet initialized.  
**Resolution:**
1. Check Postgres logs: `docker logs postgres`
2. Re-run Hive initialization script:
   ```bash
   docker exec neurostream-backend python scripts/initialize_hive.py
   ```

### Issue D: Kafka Topic Missing or Out of Disk Space
**Symptom:** `kafka.errors.NoBrokersAvailable` or `LeaderNotAvailableException`.  
**Resolution:**
1. Verify Kafka broker status:
   ```bash
   docker exec kafka /opt/kafka/bin/kafka-broker-api-versions.sh --bootstrap-server localhost:9092
   ```
2. Re-create topics explicitly:
   ```bash
   docker exec neurostream-backend python scripts/initialize_kafka.py
   ```

### Issue E: Out of Memory (OOM) during ML Training
**Symptom:** Python process killed with exit status 137.  
**Cause:** Docker Engine RAM allocation limit exceeded when loading multiple 64-channel EDF files.  
**Resolution:**
1. In Docker Desktop, open **Settings -> Resources -> Advanced** and allocate at least 8 GB (preferably 12 GB) of memory.
2. In `ml/train.py`, reduce the number of subjects loaded or downsample channels if running on constrained host hardware.

---

## 12. Teardown, Maintenance & Data Management Recipe

### Graceful Shutdown (Preserve State)
To stop all containers while preserving Kafka logs, PostgreSQL tables, and HDFS blocks:
```bash
docker compose stop
```

To resume:
```bash
docker compose start
```

### Clean Teardown (Keep Volumes)
```bash
docker compose down
```

### Complete Factory Reset (Delete All Volumes & Data)
> [!CAUTION]
> This permanently erases all ingested HDFS Parquet files, Hive Metastore tables, and Kafka topic offsets.

```bash
docker compose down -v --remove-orphans
```

To rebuild from scratch after a factory reset, execute recipes 3 -> 4 -> 5 -> 6.

