import logging
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

try:
    from backend.app.integrations.hive_client import hive_client
    from backend.app.schemas.api_schemas import HiveQueryRequest, HiveQueryResponse
except ModuleNotFoundError:
    from app.integrations.hive_client import hive_client
    from app.schemas.api_schemas import HiveQueryRequest, HiveQueryResponse

router = APIRouter(prefix="/api/hive", tags=["Apache Hive SQL"])
logger = logging.getLogger("hive-api")

@router.get("/status")
def get_hive_status():
    try:
        tables = hive_client.get_tables()
        return {
            "status": "connected",
            "database": hive_client.database,
            "host": hive_client.host,
            "port": hive_client.port,
            "tables_count": len(tables),
            "tables": tables
        }
    except Exception as e:
        logger.error(f"Hive status error: {e}")
        return {
            "status": "disconnected",
            "error": str(e)
        }

@router.get("/tables")
def list_tables():
    tables = hive_client.get_tables()
    return {"tables": tables}

@router.get("/schema/{table_name}")
def get_table_schema(table_name: str):
    schema = hive_client.get_table_schema(table_name)
    if not schema:
        raise HTTPException(status_code=404, detail=f"Table {table_name} not found or has no columns.")
    return {"table": table_name, "schema": schema}

@router.post("/query", response_model=HiveQueryResponse)
def execute_hive_query(req: HiveQueryRequest):
    query = req.query.strip().rstrip(";").strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    # Guardrails: Read-only analytics interface
    allowed_verbs = ("select", "show", "describe", "explain", "with")
    first_word = query.split()[0].lower()
    if first_word not in allowed_verbs:
        raise HTTPException(
            status_code=403,
            detail=f"Only analytical queries (SELECT, SHOW, DESCRIBE, EXPLAIN, WITH) are permitted in this console."
        )

    res = hive_client.execute_query(query)
    return res

