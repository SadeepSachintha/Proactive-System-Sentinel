import os
import sqlite3
from datetime import datetime

DB_FILE = os.path.expanduser("~/.gemini/antigravity/sentinel_db.sqlite")

def get_connection():
    """Returns a SQLite connection and ensures directory exists."""
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes tables for Sentinel audits, file operations, and resource history."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Table for file operations (Smart Organizer)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS file_ops (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        file_name TEXT NOT NULL,
        source_path TEXT NOT NULL,
        dest_path TEXT NOT NULL,
        category TEXT NOT NULL,
        reasoning TEXT,
        status TEXT NOT NULL
    )
    """)
    
    # 2. Table for system alerts
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        metric TEXT NOT NULL,
        value REAL NOT NULL,
        threshold REAL NOT NULL,
        severity TEXT NOT NULL,
        message TEXT NOT NULL
    )
    """)
    
    # 3. Table for historical metrics (for graphs/stats in CLI)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        cpu REAL NOT NULL,
        ram REAL NOT NULL,
        disk REAL NOT NULL,
        sandbox_size_mb REAL NOT NULL
    )
    """)
    
    conn.commit()
    conn.close()

# --- File Operations Helpers ---

def log_file_op(file_name: str, source_path: str, dest_path: str, category: str, reasoning: str, status: str = "SUCCESS"):
    """Logs a file organization action."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO file_ops (timestamp, file_name, source_path, dest_path, category, reasoning, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (datetime.now().isoformat(), file_name, source_path, dest_path, category, reasoning, status)
    )
    conn.commit()
    conn.close()

def get_file_ops(limit: int = 20):
    """Retrieves file organization logs."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM file_ops ORDER BY timestamp DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

# --- System Alerts Helpers ---

def log_alert(metric: str, value: float, threshold: float, severity: str, message: str):
    """Logs a system resource warning/alert."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO alerts (timestamp, metric, value, threshold, severity, message) VALUES (?, ?, ?, ?, ?, ?)",
        (datetime.now().isoformat(), metric, value, threshold, severity, message)
    )
    conn.commit()
    conn.close()

def get_alerts(limit: int = 20):
    """Retrieves system alert logs."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM alerts ORDER BY timestamp DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

# --- Metrics Helpers ---

def log_metrics(cpu: float, ram: float, disk: float, sandbox_size_mb: float):
    """Logs system resources state."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO metrics (timestamp, cpu, ram, disk, sandbox_size_mb) VALUES (?, ?, ?, ?, ?)",
        (datetime.now().isoformat(), cpu, ram, disk, sandbox_size_mb)
    )
    conn.commit()
    conn.close()

def get_latest_metrics():
    """Gets the single latest record of metrics."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM metrics ORDER BY timestamp DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_metrics_history(limit: int = 30):
    """Gets recent resource metrics records."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM metrics ORDER BY timestamp DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows
