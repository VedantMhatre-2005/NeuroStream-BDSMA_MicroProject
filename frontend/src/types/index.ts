export interface SystemService {
  status: 'connected' | 'disconnected' | 'degraded';
  endpoint: string;
}

export interface SystemStatus {
  overall_status: 'operational' | 'degraded';
  services: {
    kafka: SystemService;
    hive: SystemService;
    hdfs: SystemService;
    spark: SystemService;
  };
}

export interface ResourceUsage {
  cpu_percent: number;
  memory_percent: number;
  memory_used_mb: number;
  memory_total_mb: number;
  disk_percent: number;
}

export interface DatasetStatus {
  total_participants: number;
  total_recordings: number;
  total_size_mb: number;
  download_in_progress: boolean;
  manifest: Record<string, any>;
}

export interface Participant {
  participant_id: string;
  recording_count: number;
  recordings: Array<{
    run: string;
    filename: string;
    size_kb: number;
  }>;
}

export interface StreamingStatus {
  state: 'running' | 'paused' | 'stopped';
  participant_id?: string;
  recording_id?: string;
  replay_speed: number;
  window_duration: number;
  window_overlap: number;
  windows_published: number;
  current_window_idx: number;
  total_windows_in_recording: number;
  last_window_id?: string;
  throughput_wps: number;
  elapsed_seconds: number;
}

export interface ModelStatus {
  is_trained: boolean;
  is_training: boolean;
  version: string;
  trained_at?: string;
  algorithm: string;
  accuracy?: number;
  total_samples: number;
  classes: string[];
}

export interface ModelMetrics {
  algorithm: string;
  version: string;
  training_timestamp: string;
  total_samples: number;
  classes: string[];
  hyperparameters: Record<string, any>;
  evaluation_metrics: {
    accuracy: number;
    precision_macro: number;
    recall_macro: number;
    f1_macro: number;
    confusion_matrix: number[][];
    class_report: Record<string, any>;
  };
  top_features: Array<{ feature: string; importance: number }>;
}

export interface AnalyticsOverview {
  success: boolean;
  total_windows: number;
  total_participants: number;
  total_predictions: number;
  predictions_by_state: Record<string, { count: number; avg_confidence: number }>;
  windows_by_participant: Array<{ participant_id: string; total_windows: number }>;
}

export interface HiveQueryResult {
  success: boolean;
  columns: string[];
  rows: any[][];
  row_count: number;
  execution_time_ms: number;
  query: string;
  error?: string;
}

export interface LiveEEGMessage {
  window_id: string;
  participant_id: string;
  recording_id: string;
  start_time: number;
  end_time: number;
  predicted_class: 'left_hand' | 'right_hand' | 'rest';
  prob_left: number;
  prob_right: number;
  prob_rest: number;
  confidence: number;
  original_label: string;
  inference_latency_ms: number;
  model_version: string;
  ingestion_timestamp: string;
  classification_timestamp: string;
}

