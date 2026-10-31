# NeuroStream: Real-Time EEG Brain-State Classification and Big Data Analytics

[![Tech Stack: Kafka](https://img.shields.io/badge/Kafka-3.7.0%20KRaft-red.svg)](https://kafka.apache.org/)
[![Tech Stack: Spark](https://img.shields.io/badge/Spark-3.5.1%20Structured%20Streaming-orange.svg)](https://spark.apache.org/)
[![Tech Stack: Hadoop](https://img.shields.io/badge/Hadoop%20HDFS-3.3.6-yellow.svg)](https://hadoop.apache.org/)
[![Tech Stack: Hive](https://img.shields.io/badge/Hive-4.0.0-blue.svg)](https://hive.apache.org/)
[![Tech Stack: FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-teal.svg)](https://fastapi.tiangolo.com/)
[![Tech Stack: React](https://img.shields.io/badge/React-18.2%20+%20Vite-cyan.svg)](https://react.dev/)

An academic Big Data application demonstrating end-to-end distributed data ingestion, stream processing, machine learning inference, distributed columnar storage, and SQL analytics on real human electroencephalography (EEG) data.

---

## 1. Problem Statement & Neuroscience Background

**NeuroStream** classifies human motor imagery brain states in real-time from continuous 64-channel 160 Hz EEG recordings obtained from the official **PhysioNet EEG Motor Movement/Imagery Dataset (EEGMMIDB)**.

The system distinguishes between three brain states:
1. **Left-Hand Motor Imagery** (Contralateral mu/beta event-related desynchronization over electrode C4/Fc4).
2. **Right-Hand Motor Imagery** (Contralateral mu/beta event-related desynchronization over electrode C3/Fc3).
3. **Resting Baseline** (Bilateral sensorimotor mu synchrony).

> [!IMPORTANT]
> **Academic Demonstration Notice:** This platform is engineered for academic research, computer science, and distributed big data education. It is not intended or certified for clinical diagnostic purposes.

---

## 2. Distributed Architecture

```
               +-------------------------------------------------------+
               |        PhysioNet EEGMMIDB (64-Ch, 160 Hz EDF+)        |
               +-------------------------------------------------------+
                                          |
                                          v
               +-------------------------------------------------------+
               |             Python EEG Ingestion Service              |
               | (Notch Filter 60Hz, Bandpass 0.5-45Hz, 2s Windows)   |
               +-------------------------------------------------------+
                                          |
                                          v
               +-------------------------------------------------------+
               |               Apache Kafka 3.7.0 (KRaft)              |
               | Topic: eeg.raw.windows (5MB Producer Buffer)         |
               +-------------------------------------------------------+
                                          |
                                          v
               +-------------------------------------------------------+
               |          Apache Spark 3.5.1 Structured Streaming      |
               | 1. Butterworth 4th-Order Bandpass Filtering           |
               | 2. Welch's PSD Spectral & Statistical Features (32-D) |
               | 3. Random Forest Classifier Real-Time Inference       |
               +-------------------------------------------------------+
                     |                                         |
                     v                                         v
   +------------------------------------+   +------------------------------------+
   | Kafka: eeg.processed.features      |   | Kafka: eeg.classification.results  |
   +------------------------------------+   +------------------------------------+
                     \                                         /
                      +-------------------+-------------------+
                                          |
                                          v
               +-------------------------------------------------------+
               |               Apache Hadoop HDFS 3.3.6                |
               | Columnar Snappy-Compressed Parquet Storage Files:     |
               |   - /neurostream/features/                            |
               |   - /neurostream/predictions/                         |
               |   - /neurostream/channel_stats/                       |
               |   - /neurostream/participant_summary/                 |
               +-------------------------------------------------------+
                                          |
                                          v
               +-------------------------------------------------------+
               |            Apache Hive 4.0.0 (HiveServer2)            |
               | Metastore: PostgreSQL 15 | Database: neurostream_db   |
               +-------------------------------------------------------+
                                          |
                                          v
               +-------------------------------------------------------+
               |              FastAPI Backend Gateway                  |
               | REST API + WebSocket Broadcaster (/ws/live)           |
               +-------------------------------------------------------+
                                          |
                                          v
               +-------------------------------------------------------+
               |        React 18 + Vite + Tailwind CSS Frontend        |
               | 10 Interactive Pages, Waveform Canvas, SQL Console    |
               +-------------------------------------------------------+
```

---

## 3. Technology Stack & Pinned Versions

| Component | Technology | Version | Purpose |
|---|---|---|---|
| **Ingestion Broker** | Apache Kafka | `3.7.0` | KRaft Quorum streaming raw EEG windows |
| **Stream Processing** | Apache Spark | `3.5.1` | Structured streaming micro-batches |
| **Distributed Storage** | Apache Hadoop HDFS | `3.3.6` | Parquet columnar lake |
| **SQL Engine** | Apache Hive | `4.0.0` | External Parquet table analytics |
| **Metastore Database** | PostgreSQL | `15` | Hive Metastore catalog persistence |
| **API Gateway** | FastAPI / Uvicorn | `0.110.0` | REST endpoints & live WebSockets |
| **EEG Processing** | MNE-Python | `1.6.1` | EDF reading, montage, notch filter |
| **Machine Learning** | Scikit-Learn | `1.4.1.post1` | 32-dim Random Forest Classifier |
| **Frontend UI** | React / Vite | `18.2 / 5.1` | Clean light-theme 10-page dashboard |

---

## 4. Quick Start Guide

### Prerequisites
- Docker Desktop with WSL2 backend on Windows 11 (or Docker Engine on Linux/macOS)
- Minimum 8 GB RAM allocated to Docker Engine
- Python 3.11+ (optional for host operations)

### Step 1: Clone and Configure Environment

```powershell
# Windows PowerShell
git clone <repository_url>
cd BDSMA_MicroProject
Copy-Item .env.example .env
```

```bash
# Linux / macOS
cp .env.example .env
```

### Step 2: Start the Distributed Infrastructure

```powershell
docker compose up -d
```

Verify that all containers are healthy:
```powershell
docker compose ps
```

### Step 3: Download Real PhysioNet Recordings

```powershell
docker exec neurostream-backend python scripts/download_dataset.py
```
This downloads 9 real EDF recordings from PhysioNet for subjects `S001`, `S002`, `S003` (Runs `R04`, `R08`, `R12`).

### Step 4: Train Machine Learning Model

```powershell
docker exec neurostream-backend python ml/train.py
```
Extracts 1,110 real 2-second windows, computes 32 features per window, and fits a balanced Random Forest Classifier.

### Step 5: Populate HDFS Parquet Lake & Apache Hive

```powershell
docker exec neurostream-backend python scripts/populate_hdfs_hive.py
```
Writes Snappy Parquet files into HDFS directories and verifies that HiveServer2 returns live results.

### Step 6: Run Comprehensive Test Suite

```powershell
docker exec neurostream-backend pytest tests/test_end_to_end.py -v
```

### Step 7: Access the User Interface

Open your browser to:
- **Frontend Dashboard:** [http://localhost:3000](http://localhost:3000)
- **FastAPI Interactive Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Hadoop NameNode Web UI:** [http://localhost:9870](http://localhost:9870)
- **Spark Master UI:** [http://localhost:8080](http://localhost:8080)
- **HiveServer2 Web UI:** [http://localhost:10002](http://localhost:10002)

---

## 5. Machine Learning & Feature Engineering

Each 2.0-second EEG window (320 samples at 160 Hz) is transformed into a **32-dimensional feature vector**:

1. **Global Statistical Moments (6 features):**
   - Mean amplitude, standard deviation, RMS amplitude, signal variance, minimum amplitude, maximum amplitude.
2. **Global Spectral Band Powers (Welch's PSD, 5 features):**
   - Delta (0.5–4 Hz), Theta (4–8 Hz), Alpha/Mu (8–13 Hz), Beta (13–30 Hz), Gamma (30–45 Hz).
3. **Relative Band Powers (5 features):**
   - Normalized ratio of each frequency band power to total spectral power.
4. **Sensorimotor Channel-Specific Spectral Features (14 features):**
   - Alpha and Beta band power specifically extracted from motor cortex electrodes: `C3`, `C4`, `Cz`, `Fc3`, `Fc4`, `Cp3`, `Cp4`.
5. **Hemispheric Lateralization Indices (2 features):**
   - Mu/Alpha lateralization index: $\text{LI}_{\alpha} = \frac{C_3 - C_4}{C_3 + C_4}$
   - Beta lateralization index: $\text{LI}_{\beta} = \frac{C_3 - C_4}{C_3 + C_4}$

---

## 6. Apache Hive Analytics Query Catalog

The system provides 8 pre-configured analytical SQL queries executed directly against HiveServer2:

1. **Total windows processed per participant:**
   ```sql
   SELECT participant_id, COUNT(*) AS total_windows
   FROM eeg_window_features
   GROUP BY participant_id
   ORDER BY total_windows DESC;
   ```
2. **Distribution of predicted brain states:**
   ```sql
   SELECT predicted_class, COUNT(*) AS count, ROUND(AVG(confidence), 4) AS avg_confidence
   FROM eeg_classification_results
   GROUP BY predicted_class;
   ```
3. **Average band power by brain state:**
   ```sql
   SELECT c.predicted_class,
          ROUND(AVG(f.delta_power), 2) AS avg_delta,
          ROUND(AVG(f.alpha_power), 2) AS avg_alpha,
          ROUND(AVG(f.beta_power), 2) AS avg_beta
   FROM eeg_window_features f
   JOIN eeg_classification_results c ON f.window_id = c.window_id
   GROUP BY c.predicted_class;
   ```
4. **Channel-wise activity comparisons:**
   ```sql
   SELECT channel_name, ROUND(AVG(variance), 2) AS avg_variance, ROUND(AVG(beta_power), 2) AS avg_beta
   FROM eeg_channel_statistics
   GROUP BY channel_name
   ORDER BY avg_beta DESC LIMIT 20;
   ```
5. **Participant-wise classification distribution:**
   ```sql
   SELECT participant_id, predicted_class, COUNT(*) AS prediction_count
   FROM eeg_classification_results
   GROUP BY participant_id, predicted_class;
   ```
6. **Task-wise Beta/Alpha power ratio:**
   ```sql
   SELECT original_label, ROUND(AVG(beta_power / NULLIF(alpha_power, 0)), 3) AS beta_alpha_ratio
   FROM eeg_window_features
   GROUP BY original_label;
   ```
7. **Temporal prediction rate:**
   ```sql
   SELECT SUBSTR(classification_timestamp, 1, 16) AS time_minute,
          COUNT(*) AS predictions_per_minute,
          ROUND(AVG(inference_latency_ms), 2) AS avg_latency_ms
   FROM eeg_classification_results
   GROUP BY SUBSTR(classification_timestamp, 1, 16)
   ORDER BY time_minute DESC LIMIT 30;
   ```
8. **Classification counts by recording:**
   ```sql
   SELECT recording_id, COUNT(*) AS total_predictions,
          SUM(CASE WHEN predicted_class = 'left_hand' THEN 1 ELSE 0 END) AS left_hand_count,
          SUM(CASE WHEN predicted_class = 'right_hand' THEN 1 ELSE 0 END) AS right_hand_count,
          SUM(CASE WHEN predicted_class = 'rest' THEN 1 ELSE 0 END) AS rest_count
   FROM eeg_classification_results
   GROUP BY recording_id;
   ```

---

## 7. Frontend Application (10 Pages)

1. **Overview Dashboard (`/`):** KPI summary cards, pipeline architecture status, brain-state distribution bar charts, and quick-launch action triggers.
2. **Live Monitoring (`/live`):** Smooth 60fps multi-channel EEG trace viewer canvas with playback controls (play, pause, speed multipliers 0.5x–5x), real-time prediction card with probability gauges, and live ingestion feed table.
3. **EEG Explorer (`/explorer`):** High-resolution multi-channel EEG waveform explorer with time sliders, 0.5–45 Hz bandpass filter toggle, and PhysioNet annotation timeline markers (T0, T1, T2).
4. **Brain-State ML (`/classification`):** Sensorimotor Mu/Beta rhythm ERD/ERS dynamics breakdown, contralateral desynchronization analysis, and comparative electrophysiological radar chart.
5. **Signal Analytics (`/analytics`):** Frequency band decomposition (Delta, Theta, Alpha, Beta, Gamma), Welch PSD power curves, and top active channels ranked by variance and beta power.
6. **Participants (`/participants`):** Ingested subject cards (S001, S002, S003), recording file manifests, and per-subject prediction summaries.
7. **Hive Analytics (`/hive`):** Interactive SQL query editor with preset queries, execution timer, dynamic results table with CSV export, and table schema explorer.
8. **Model Evaluation (`/model`):** Empirical 3x3 confusion matrix heatmap, classification performance metrics (Accuracy, Macro Precision, Recall, F1), top-10 Gini feature importances, and one-click model retrain trigger.
9. **System Monitoring (`/system`):** Distributed node health indicators, live CPU / RAM / Disk telemetry, Kafka topic status, and HDFS cluster capacity.
10. **Settings (`/settings`):** Pipeline parameters, window durations, cluster endpoints, and academic research citations.

---

## 8. References & Citations

- **Dataset:** Goldberger, A., Amaral, L., Glass, L., Hausdorff, J., Ivanov, P. C., Mark, R., ... & Stanley, H. E. (2000). PhysioBank, PhysioToolkit, and PhysioNet: Components of a new research resource for complex physiologic signals. *Circulation*, 101(23), e215-e220.
- **BCI2000 System:** Schalk, G., McFarland, D.J., Hinterberger, T., Birbaumer, N., Wolpaw, J.R. (2004). BCI2000: A General-Purpose Brain-Computer Interface (BCI) System. *IEEE Transactions on Biomedical Engineering*, 51(6):1034-1043.

