USE neurostream_db;

-- 1. EEG Window Features Table
CREATE EXTERNAL TABLE IF NOT EXISTS eeg_window_features (
    window_id STRING,
    participant_id STRING,
    recording_id STRING,
    start_time DOUBLE,
    end_time DOUBLE,
    mean_amplitude DOUBLE,
    std_amplitude DOUBLE,
    rms_amplitude DOUBLE,
    variance DOUBLE,
    min_amplitude DOUBLE,
    max_amplitude DOUBLE,
    delta_power DOUBLE,
    theta_power DOUBLE,
    alpha_power DOUBLE,
    beta_power DOUBLE,
    gamma_power DOUBLE,
    relative_delta DOUBLE,
    relative_theta DOUBLE,
    relative_alpha DOUBLE,
    relative_beta DOUBLE,
    relative_gamma DOUBLE,
    original_label STRING,
    ingestion_timestamp STRING,
    processing_timestamp STRING
)
STORED AS PARQUET
LOCATION '/neurostream/features';

-- 2. EEG Channel Statistics Table
CREATE EXTERNAL TABLE IF NOT EXISTS eeg_channel_statistics (
    window_id STRING,
    participant_id STRING,
    recording_id STRING,
    channel_name STRING,
    mean DOUBLE,
    std DOUBLE,
    rms DOUBLE,
    variance DOUBLE,
    min_val DOUBLE,
    max_val DOUBLE,
    alpha_power DOUBLE,
    beta_power DOUBLE,
    stat_timestamp STRING
)
STORED AS PARQUET
LOCATION '/neurostream/channel_stats';

-- 3. EEG Classification Results Table
CREATE EXTERNAL TABLE IF NOT EXISTS eeg_classification_results (
    window_id STRING,
    participant_id STRING,
    recording_id STRING,
    start_time DOUBLE,
    end_time DOUBLE,
    predicted_class STRING,
    prob_left DOUBLE,
    prob_right DOUBLE,
    prob_rest DOUBLE,
    confidence DOUBLE,
    original_label STRING,
    inference_latency_ms DOUBLE,
    model_version STRING,
    ingestion_timestamp STRING,
    classification_timestamp STRING
)
STORED AS PARQUET
LOCATION '/neurostream/predictions';

-- 4. EEG Participant Summary Table
CREATE TABLE IF NOT EXISTS eeg_participant_summary (
    participant_id STRING,
    total_windows INT,
    total_left_predictions INT,
    total_right_predictions INT,
    total_rest_predictions INT,
    avg_alpha_power DOUBLE,
    avg_beta_power DOUBLE,
    avg_latency_ms DOUBLE,
    last_updated STRING
)
STORED AS PARQUET
LOCATION '/neurostream/participant_summary';
