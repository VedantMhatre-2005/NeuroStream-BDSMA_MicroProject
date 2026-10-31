from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

# System Schemas
class ServiceStatus(BaseModel):
    status: str
    endpoint: str

class SystemStatusResponse(BaseModel):
    overall_status: str
    services: Dict[str, ServiceStatus]

class ResourceUsage(BaseModel):
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_total_mb: float
    disk_percent: float

# Dataset Schemas
class DownloadRequest(BaseModel):
    participants: List[str] = Field(default_factory=lambda: ["S001"])
    runs: List[str] = Field(default_factory=lambda: ["R04", "R08", "R12"])

class DatasetStatusResponse(BaseModel):
    total_participants: int
    total_recordings: int
    total_size_mb: float
    download_in_progress: bool
    manifest: Dict[str, Any]

# Streaming Schemas
class StreamingStartRequest(BaseModel):
    participant_id: Optional[str] = None
    recording_id: Optional[str] = None
    speed_factor: float = 1.0
    loop: bool = False

class StreamingStatusResponse(BaseModel):
    is_running: bool
    is_paused: bool
    participant_id: Optional[str]
    recording_id: Optional[str]
    speed_factor: float
    current_window: int
    total_windows: int
    windows_sent: int
    elapsed_seconds: float

# ML Schemas
class TrainRequest(BaseModel):
    n_estimators: int = 100
    test_size: float = 0.25
    random_state: int = 42

class ModelMetricsResponse(BaseModel):
    model_version: str
    trained_at: str
    accuracy: float
    precision_macro: float
    recall_macro: float
    f1_macro: float
    confusion_matrix: List[List[int]]
    classes: List[str]
    feature_importances: List[Dict[str, Any]]
    total_samples: int

# Hive Query Schemas
class HiveQueryRequest(BaseModel):
    query: str

class HiveQueryResponse(BaseModel):
    success: bool
    columns: List[str]
    rows: List[List[Any]]
    row_count: int
    execution_time_ms: float
    query: str
    error: Optional[str] = None

