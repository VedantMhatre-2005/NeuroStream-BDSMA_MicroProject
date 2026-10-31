USE neurostream_db;

-- Query 1: Total windows processed per participant
SELECT participant_id, COUNT(*) AS total_windows
FROM eeg_window_features
GROUP BY participant_id
ORDER BY total_windows DESC;

-- Query 2: Distribution of predicted brain states
SELECT predicted_class, COUNT(*) AS count, ROUND(AVG(confidence), 4) AS avg_confidence
FROM eeg_classification_results
GROUP BY predicted_class;

-- Query 3: Average band power by brain state
SELECT 
    c.predicted_class,
    ROUND(AVG(f.delta_power), 4) AS avg_delta,
    ROUND(AVG(f.theta_power), 4) AS avg_theta,
    ROUND(AVG(f.alpha_power), 4) AS avg_alpha,
    ROUND(AVG(f.beta_power), 4) AS avg_beta,
    ROUND(AVG(f.gamma_power), 4) AS avg_gamma
FROM eeg_window_features f
JOIN eeg_classification_results c ON f.window_id = c.window_id
GROUP BY c.predicted_class;

-- Query 4: Channel-wise activity comparisons
SELECT 
    channel_name,
    ROUND(AVG(mean), 4) AS avg_mean,
    ROUND(AVG(variance), 4) AS avg_variance,
    ROUND(AVG(alpha_power), 4) AS avg_alpha,
    ROUND(AVG(beta_power), 4) AS avg_beta
FROM eeg_channel_statistics
GROUP BY channel_name
ORDER BY avg_beta DESC
LIMIT 20;

-- Query 5: Participant-wise classification distribution
SELECT 
    participant_id,
    predicted_class,
    COUNT(*) AS prediction_count
FROM eeg_classification_results
GROUP BY participant_id, predicted_class
ORDER BY participant_id, prediction_count DESC;

-- Query 6: Alpha and beta power comparisons by original task label
SELECT 
    original_label,
    COUNT(*) AS window_count,
    ROUND(AVG(alpha_power), 4) AS avg_alpha,
    ROUND(AVG(beta_power), 4) AS avg_beta,
    ROUND(AVG(beta_power / NULLIF(alpha_power, 0)), 4) AS beta_alpha_ratio
FROM eeg_window_features
GROUP BY original_label;

-- Query 7: Temporal distribution of predictions
SELECT 
    SUBSTR(classification_timestamp, 1, 16) AS time_minute,
    COUNT(*) AS predictions_per_minute,
    ROUND(AVG(inference_latency_ms), 2) AS avg_latency_ms
FROM eeg_classification_results
GROUP BY SUBSTR(classification_timestamp, 1, 16)
ORDER BY time_minute DESC
LIMIT 30;

-- Query 8: Classification counts by recording
SELECT 
    recording_id,
    COUNT(*) AS total_predictions,
    SUM(CASE WHEN predicted_class = 'left_hand' THEN 1 ELSE 0 END) AS left_hand_count,
    SUM(CASE WHEN predicted_class = 'right_hand' THEN 1 ELSE 0 END) AS right_hand_count,
    SUM(CASE WHEN predicted_class = 'rest' THEN 1 ELSE 0 END) AS rest_count
FROM eeg_classification_results
GROUP BY recording_id
ORDER BY total_predictions DESC;

