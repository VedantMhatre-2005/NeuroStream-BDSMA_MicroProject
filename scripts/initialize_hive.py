#!/usr/bin/env python3
"""
Initialize Hive Database and Tables for NeuroStream
Executes DDL statements to set up neurostream_db and tables.
"""

import os
import sys
import time

def init_via_pyhive():
    try:
        from pyhive import hive
        print("Connecting to HiveServer2 via PyHive...")
        conn = hive.Connection(host="localhost", port=10000, username="hive")
        cursor = conn.cursor()

        print("Creating database neurostream_db...")
        cursor.execute("CREATE DATABASE IF NOT EXISTS neurostream_db")
        cursor.execute("USE neurostream_db")

        # Read create_tables.sql
        script_dir = os.path.dirname(os.path.abspath(__file__))
        sql_path = os.path.join(script_dir, "..", "hive", "sql", "create_tables.sql")
        
        with open(sql_path, "r") as f:
            content = f.read()

        # Split into individual statements
        statements = [s.strip() for s in content.split(";") if s.strip() and not s.strip().startswith("--")]
        for stmt in statements:
            print(f"Executing: {stmt[:60]}...")
            cursor.execute(stmt)

        print("Hive tables initialized successfully via PyHive.")
        return 0
    except Exception as e:
        print(f"PyHive initialization failed: {e}")
        return 1

def init_via_beeline():
    import subprocess
    print("Attempting initialization via docker exec beeline...")
    cmd = [
        "docker", "exec", "-i", "hive-server",
        "beeline", "-u", "jdbc:hive2://localhost:10000", "-n", "hive",
        "-f", "/opt/hive/sql/create_tables.sql"
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        print(res.stdout)
        if res.returncode == 0:
            print("Hive tables initialized successfully via Beeline.")
            return 0
        else:
            print(f"Beeline error: {res.stderr}")
            return 1
    except Exception as e:
        print(f"Beeline execution error: {e}")
        return 1

if __name__ == "__main__":
    ret = init_via_pyhive()
    if ret != 0:
        ret = init_via_beeline()
    sys.exit(ret)

