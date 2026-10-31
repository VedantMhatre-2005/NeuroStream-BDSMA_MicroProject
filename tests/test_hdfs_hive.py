import pytest
import requests
try:
    from backend.app.services.hdfs_service import hdfs_service
    from backend.app.integrations.hive_client import hive_client
except ModuleNotFoundError:
    from app.services.hdfs_service import hdfs_service
    from app.integrations.hive_client import hive_client

def test_hdfs_connectivity_and_files():
    """Verify HDFS has directories and parquet files."""
    features_files = hdfs_service.list_dir("/neurostream/features")
    assert len(features_files) > 0, "No files found in /neurostream/features"

    predictions_files = hdfs_service.list_dir("/neurostream/predictions")
    assert len(predictions_files) > 0, "No files found in /neurostream/predictions"

    channel_stats_files = hdfs_service.list_dir("/neurostream/channel_stats")
    assert len(channel_stats_files) > 0, "No files found in /neurostream/channel_stats"

    summary_files = hdfs_service.list_dir("/neurostream/participant_summary")
    assert len(summary_files) > 0, "No files found in /neurostream/participant_summary"

def test_hive_tables_exist():
    """Verify all 4 Hive tables exist in neurostream_db."""
    tables = hive_client.get_tables()
    expected = ["eeg_channel_statistics", "eeg_classification_results", "eeg_participant_summary", "eeg_window_features"]
    for exp in expected:
        assert exp in tables, f"Expected table {exp} not in Hive tables: {tables}"

def test_hive_queries_return_data():
    """Verify standard Hive analytics queries return genuine rows."""
    # 1. Total windows per participant
    res1 = hive_client.get_windows_per_participant()
    assert res1["success"] is True
    assert res1["row_count"] >= 3
    assert len(res1["rows"]) >= 3

    # 2. Brain state predictions distribution
    res2 = hive_client.get_brain_states_distribution()
    assert res2["success"] is True
    assert res2["row_count"] == 3 # left_hand, right_hand, rest

    # 3. Channel activity
    res3 = hive_client.get_channel_activity(limit=10)
    assert res3["success"] is True
    assert res3["row_count"] > 0
