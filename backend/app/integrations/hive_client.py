import time
import logging
from typing import List, Dict, Any, Optional
from pyhive import hive
try:
    from backend.app.config import settings
except ModuleNotFoundError:
    from app.config import settings

logger = logging.getLogger("neurostream-hive")

class HiveClient:
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        database: Optional[str] = None,
        username: str = "hive"
    ):
        self.host = host or settings.HIVE_HOST
        self.port = port or settings.HIVE_PORT
        self.database = database or settings.HIVE_DATABASE
        self.username = username

    def get_connection(self):
        """
        Creates a new connection to HiveServer2.
        """
        return hive.Connection(
            host=self.host,
            port=self.port,
            database=self.database,
            username=self.username
        )

    def execute_query(self, query: str) -> Dict[str, Any]:
        """
        Executes a SQL query against Hive and returns columns and row values.
        """
        clean_query = query.strip().rstrip(";").strip()
        start_time = time.time()
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SET hive.auto.convert.join=false")
            cursor.execute(clean_query)

            columns = []
            if cursor.description:
                # Strip table name prefix if present (e.g. 'eeg_window_features.window_id' -> 'window_id')
                columns = [col[0].split(".")[-1] for col in cursor.description]

            rows = cursor.fetchall()
            execution_time_ms = round((time.time() - start_time) * 1000.0, 2)

            # Convert row tuples to lists with serializable values
            formatted_rows = []
            for row in rows:
                formatted_rows.append([
                    float(val) if isinstance(val, (int, float)) and not isinstance(val, bool) and '.' in str(val)
                    else val for val in row
                ])

            return {
                "success": True,
                "columns": columns,
                "rows": formatted_rows,
                "row_count": len(rows),
                "execution_time_ms": execution_time_ms,
                "query": query.strip()
            }
        except Exception as e:
            execution_time_ms = round((time.time() - start_time) * 1000.0, 2)
            logger.error(f"Error executing Hive query: {e}")
            return {
                "success": False,
                "columns": [],
                "rows": [],
                "row_count": 0,
                "execution_time_ms": execution_time_ms,
                "query": query.strip(),
                "error": str(e)
            }
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def get_tables(self) -> List[str]:
        res = self.execute_query("SHOW TABLES")
        if res["success"]:
            return [row[0] for row in res["rows"]]
        return []

    def get_table_schema(self, table_name: str) -> List[Dict[str, str]]:
        res = self.execute_query(f"DESCRIBE {table_name}")
        schema = []
        if res["success"]:
            for row in res["rows"]:
                if len(row) >= 2 and row[0] and not row[0].startswith("#"):
                    schema.append({"column": row[0].strip(), "type": row[1].strip()})
        return schema

    # Standard Analytics Queries
    def get_windows_per_participant(self) -> Dict[str, Any]:
        query = """
        SELECT participant_id, COUNT(*) AS total_windows
        FROM eeg_window_features
        GROUP BY participant_id
        ORDER BY total_windows DESC
        """
        return self.execute_query(query)

    def get_brain_states_distribution(self) -> Dict[str, Any]:
        query = """
        SELECT predicted_class, COUNT(*) AS count, ROUND(AVG(confidence), 4) AS avg_confidence
        FROM eeg_classification_results
        GROUP BY predicted_class
        """
        return self.execute_query(query)

    def get_band_power_by_state(self) -> Dict[str, Any]:
        query = """
        SELECT 
            c.predicted_class,
            ROUND(AVG(f.delta_power), 4) AS avg_delta,
            ROUND(AVG(f.theta_power), 4) AS avg_theta,
            ROUND(AVG(f.alpha_power), 4) AS avg_alpha,
            ROUND(AVG(f.beta_power), 4) AS avg_beta,
            ROUND(AVG(f.gamma_power), 4) AS avg_gamma
        FROM eeg_window_features f
        JOIN eeg_classification_results c ON f.window_id = c.window_id
        GROUP BY c.predicted_class
        """
        return self.execute_query(query)

    def get_channel_activity(self, limit: int = 20) -> Dict[str, Any]:
        query = f"""
        SELECT 
            channel_name,
            ROUND(AVG(mean), 4) AS avg_mean,
            ROUND(AVG(variance), 4) AS avg_variance,
            ROUND(AVG(alpha_power), 4) AS avg_alpha,
            ROUND(AVG(beta_power), 4) AS avg_beta
        FROM eeg_channel_statistics
        GROUP BY channel_name
        ORDER BY avg_beta DESC
        LIMIT {limit}
        """
        return self.execute_query(query)

    def get_participant_predictions(self) -> Dict[str, Any]:
        query = """
        SELECT 
            participant_id,
            predicted_class,
            COUNT(*) AS prediction_count
        FROM eeg_classification_results
        GROUP BY participant_id, predicted_class
        ORDER BY participant_id, prediction_count DESC
        """
        return self.execute_query(query)

    def get_band_power_by_task(self) -> Dict[str, Any]:
        query = """
        SELECT 
            original_label,
            COUNT(*) AS window_count,
            ROUND(AVG(alpha_power), 4) AS avg_alpha,
            ROUND(AVG(beta_power), 4) AS avg_beta,
            ROUND(AVG(beta_power / NULLIF(alpha_power, 0)), 4) AS beta_alpha_ratio
        FROM eeg_window_features
        GROUP BY original_label
        """
        return self.execute_query(query)

    def get_temporal_predictions(self, limit: int = 30) -> Dict[str, Any]:
        query = f"""
        SELECT 
            SUBSTR(classification_timestamp, 1, 16) AS time_minute,
            COUNT(*) AS predictions_per_minute,
            ROUND(AVG(inference_latency_ms), 2) AS avg_latency_ms
        FROM eeg_classification_results
        GROUP BY SUBSTR(classification_timestamp, 1, 16)
        ORDER BY time_minute DESC
        LIMIT {limit}
        """
        return self.execute_query(query)

    def get_predictions_by_recording(self) -> Dict[str, Any]:
        query = """
        SELECT 
            recording_id,
            COUNT(*) AS total_predictions,
            SUM(CASE WHEN predicted_class = 'left_hand' THEN 1 ELSE 0 END) AS left_hand_count,
            SUM(CASE WHEN predicted_class = 'right_hand' THEN 1 ELSE 0 END) AS right_hand_count,
            SUM(CASE WHEN predicted_class = 'rest' THEN 1 ELSE 0 END) AS rest_count
        FROM eeg_classification_results
        GROUP BY recording_id
        ORDER BY total_predictions DESC
        """
        return self.execute_query(query)

hive_client = HiveClient()
