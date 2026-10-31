#!/usr/bin/env python3
"""
NeuroStream Health Check Script
Verifies connectivity across all Big Data infrastructure services.
"""

import socket
import sys
import json
import time
import urllib.request

SERVICES = [
    {"name": "PostgreSQL Metastore", "host": "localhost", "port": 5432, "critical": True},
    {"name": "Kafka Broker (External)", "host": "localhost", "port": 29092, "critical": True},
    {"name": "HDFS NameNode (Web UI)", "host": "localhost", "port": 9870, "critical": True},
    {"name": "HDFS NameNode (IPC)", "host": "localhost", "port": 9000, "critical": True},
    {"name": "HDFS DataNode (Web UI)", "host": "localhost", "port": 9864, "critical": False},
    {"name": "Hive Metastore", "host": "localhost", "port": 9083, "critical": True},
    {"name": "HiveServer2", "host": "localhost", "port": 10000, "critical": True},
    {"name": "Spark Master (Web UI)", "host": "localhost", "port": 8080, "critical": True},
    {"name": "Spark Master (IPC)", "host": "localhost", "port": 7077, "critical": True},
    {"name": "FastAPI Backend", "host": "localhost", "port": 8000, "path": "/api/health", "critical": False},
    {"name": "React Frontend", "host": "localhost", "port": 3000, "critical": False},
]

def check_tcp_port(host: str, port: int, timeout: float = 3.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False

def check_http_endpoint(host: str, port: int, path: str = "/", timeout: float = 3.0) -> bool:
    url = f"http://{host}:{port}{path}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "NeuroStream-HealthCheck"})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.status in (200, 204, 301, 302)
    except Exception:
        return False

def run_health_checks():
    print("=" * 60)
    print(" NeuroStream Infrastructure Health Check")
    print("=" * 60)
    results = {}
    all_critical_ok = True

    for svc in SERVICES:
        name = svc["name"]
        host = svc["host"]
        port = svc["port"]
        path = svc.get("path")
        critical = svc.get("critical", False)

        if path:
            is_ok = check_http_endpoint(host, port, path)
        else:
            is_ok = check_tcp_port(host, port)

        status_str = "ONLINE  [OK]" if is_ok else "OFFLINE [FAILED]"
        crit_str = "(CRITICAL)" if critical else "(OPTIONAL)"
        print(f"[{status_str}] {name:30} {host}:{port} {crit_str}")

        results[name] = {"online": is_ok, "port": port, "critical": critical}
        if critical and not is_ok:
            all_critical_ok = False

    print("=" * 60)
    if all_critical_ok:
        print("ALL CRITICAL SERVICES ARE HEALTHY AND ACCESSIBLE!")
        return 0
    else:
        print("SOME CRITICAL SERVICES ARE NOT REACHABLE. Review container logs.")
        return 1

if __name__ == "__main__":
    sys.exit(run_health_checks())

