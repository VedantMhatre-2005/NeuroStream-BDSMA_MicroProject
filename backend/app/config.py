import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    FASTAPI_PORT: int = 8000
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    TOPIC_RAW_WINDOWS: str = os.getenv("TOPIC_RAW_WINDOWS", "eeg.raw.windows")
    TOPIC_PROCESSED_FEATURES: str = os.getenv("TOPIC_PROCESSED_FEATURES", "eeg.processed.features")
    TOPIC_CLASSIFICATION_RESULTS: str = os.getenv("TOPIC_CLASSIFICATION_RESULTS", "eeg.classification.results")
    TOPIC_PROCESSING_ERRORS: str = os.getenv("TOPIC_PROCESSING_ERRORS", "eeg.processing.errors")
    
    HADOOP_NAMENODE_URL: str = os.getenv("HADOOP_NAMENODE_URL", "hdfs://namenode:9000")
    HDFS_BASE_DIR: str = os.getenv("HDFS_BASE_DIR", "/neurostream")
    
    HIVE_HOST: str = os.getenv("HIVE_HOST", "hive-server")
    HIVE_PORT: int = int(os.getenv("HIVE_PORT", "10000"))
    HIVE_DATABASE: str = os.getenv("HIVE_DATABASE", "neurostream_db")
    
    SPARK_MASTER: str = os.getenv("SPARK_MASTER", "spark://spark-master:7077")
    
    DATA_DIR: str = os.getenv("DATA_DIR", "/app/data")
    MODELS_DIR: str = os.getenv("MODELS_DIR", "/app/data/models")
    CHECKPOINT_DIR: str = os.getenv("CHECKPOINT_DIR", "/app/data/checkpoints")

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()

