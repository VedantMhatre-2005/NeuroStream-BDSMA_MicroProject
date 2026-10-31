import io
import json
import logging
from typing import List, Dict, Any, Optional
import requests
import pyarrow as pa
import pyarrow.parquet as pq

try:
    from backend.app.config import settings
except ModuleNotFoundError:
    from app.config import settings

logger = logging.getLogger("neurostream-hdfs")

class HDFSService:
    def __init__(self, namenode_web_url: str = "http://namenode:9870/webhdfs/v1"):
        self.webhdfs_url = namenode_web_url

    def write_parquet(self, hdfs_path: str, records: List[Dict[str, Any]], schema: Optional[pa.Schema] = None) -> bool:
        """
        Writes a list of dictionaries as a Parquet file to HDFS via WebHDFS.
        """
        if not records:
            logger.warning(f"No records provided to write to {hdfs_path}")
            return False

        try:
            # Create PyArrow Table
            if schema:
                table = pa.Table.from_pylist(records, schema=schema)
            else:
                table = pa.Table.from_pylist(records)

            # Write to in-memory Parquet buffer
            buffer = io.BytesIO()
            pq.write_table(table, buffer, compression="SNAPPY")
            parquet_data = buffer.getvalue()

            # Ensure leading slash in hdfs_path
            norm_path = hdfs_path if hdfs_path.startswith("/") else f"/{hdfs_path}"
            create_url = f"{self.webhdfs_url}{norm_path}?op=CREATE&overwrite=true"

            # Step 1: Request NameNode for datanode redirect
            resp = requests.put(create_url, allow_redirects=False, timeout=10)
            if resp.status_code != 307:
                logger.error(f"NameNode WebHDFS CREATE failed with status {resp.status_code}: {resp.text}")
                return False

            datanode_location = resp.headers.get("Location")
            if not datanode_location:
                logger.error("NameNode did not provide Location header for DataNode upload.")
                return False

            # Step 2: Upload bytes to DataNode
            upload_resp = requests.put(
                datanode_location,
                data=parquet_data,
                headers={"Content-Type": "application/octet-stream"},
                timeout=30
            )

            if upload_resp.status_code in (200, 201):
                logger.info(f"Successfully wrote {len(records)} records as Parquet to {hdfs_path} ({len(parquet_data)} bytes)")
                return True
            else:
                logger.error(f"DataNode WebHDFS upload failed with status {upload_resp.status_code}: {upload_resp.text}")
                return False

        except Exception as e:
            logger.error(f"Exception writing Parquet to HDFS ({hdfs_path}): {e}")
            return False

    def list_dir(self, hdfs_path: str) -> List[Dict[str, Any]]:
        """
        Lists files in an HDFS directory.
        """
        norm_path = hdfs_path if hdfs_path.startswith("/") else f"/{hdfs_path}"
        url = f"{self.webhdfs_url}{norm_path}?op=LISTSTATUS"
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("FileStatuses", {}).get("FileStatus", [])
            else:
                logger.warning(f"WebHDFS LISTSTATUS returned {resp.status_code} for {hdfs_path}")
                return []
        except Exception as e:
            logger.error(f"Exception listing HDFS directory {hdfs_path}: {e}")
            return []

    def file_exists(self, hdfs_path: str) -> bool:
        """
        Checks whether an HDFS path exists.
        """
        norm_path = hdfs_path if hdfs_path.startswith("/") else f"/{hdfs_path}"
        url = f"{self.webhdfs_url}{norm_path}?op=GETFILESTATUS"
        try:
            resp = requests.get(url, timeout=5)
            return resp.status_code == 200
        except Exception:
            return False

    def delete_path(self, hdfs_path: str, recursive: bool = True) -> bool:
        """
        Deletes a path in HDFS.
        """
        norm_path = hdfs_path if hdfs_path.startswith("/") else f"/{hdfs_path}"
        url = f"{self.webhdfs_url}{norm_path}?op=DELETE&recursive={str(recursive).lower()}"
        try:
            resp = requests.delete(url, timeout=10)
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"Exception deleting {hdfs_path}: {e}")
            return False

hdfs_service = HDFSService()
