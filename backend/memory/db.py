import sqlite3
import json
import os
from typing import Optional, Dict, Any, List
from datetime import datetime

DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "ai_os_memory.db")

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def init_db():
    """Initializes the SQLite schema for user preferences, execution history, and memory facts."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Preferences Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS preferences (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                description TEXT DEFAULT '',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # 2. Task History Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_query TEXT NOT NULL,
                plan_json TEXT,
                status TEXT NOT NULL,
                logs_json TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 3. Memory Facts / Workflow Notes Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Populate default preferences if empty
        cursor.execute("SELECT COUNT(*) FROM preferences;")
        if cursor.fetchone()[0] == 0:
            default_prefs = [
                ("default_browser", "chrome", "Preferred web browser"),
                ("editor", "code", "Preferred text editor command (e.g. code, notepad)"),
                ("user_name", "User", "User display name")
            ]
            cursor.executemany(
                "INSERT INTO preferences (key, value, description) VALUES (?, ?, ?);", 
                default_prefs
            )
        conn.commit()

# --- Preference Operations ---

def set_preference(key: str, value: str, description: str = "") -> dict:
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO preferences (key, value, description, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                description = CASE WHEN excluded.description != '' THEN excluded.description ELSE preferences.description END,
                updated_at = CURRENT_TIMESTAMP;
        """, (key.strip().lower(), str(value).strip(), description.strip()))
        conn.commit()
    return {"key": key.strip().lower(), "value": value}

def get_preference(key: str, default: Optional[str] = None) -> Optional[str]:
    with get_connection() as conn:
        row = conn.execute("SELECT value FROM preferences WHERE key = ?;", (key.strip().lower(),)).fetchone()
        if row:
            return row["value"]
    return default

def get_all_preferences() -> Dict[str, str]:
    with get_connection() as conn:
        rows = conn.execute("SELECT key, value FROM preferences ORDER BY key ASC;").fetchall()
        return {r["key"]: r["value"] for r in rows}

def delete_preference(key: str) -> bool:
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM preferences WHERE key = ?;", (key.strip().lower(),))
        conn.commit()
        return cursor.rowcount > 0

# --- Task History Operations ---

def log_task(user_query: str, plan: Optional[dict] = None, status: str = "completed", logs: Optional[List[str]] = None) -> int:
    with get_connection() as conn:
        plan_str = json.dumps(plan) if plan else None
        logs_str = json.dumps(logs) if logs else None
        cursor = conn.execute("""
            INSERT INTO task_history (user_query, plan_json, status, logs_json, timestamp)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP);
        """, (user_query, plan_str, status, logs_str))
        conn.commit()
        return cursor.lastrowid

def get_recent_tasks(limit: int = 10) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT id, user_query, status, timestamp, plan_json, logs_json
            FROM task_history 
            ORDER BY id DESC 
            LIMIT ?;
        """, (limit,)).fetchall()
        
        results = []
        for r in rows:
            results.append({
                "id": r["id"],
                "user_query": r["user_query"],
                "status": r["status"],
                "timestamp": r["timestamp"],
                "plan": json.loads(r["plan_json"]) if r["plan_json"] else None,
                "logs": json.loads(r["logs_json"]) if r["logs_json"] else []
            })
        return results

def search_tasks(keyword: str, limit: int = 5) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT id, user_query, status, timestamp 
            FROM task_history 
            WHERE user_query LIKE ? 
            ORDER BY id DESC 
            LIMIT ?;
        """, (f"%{keyword}%", limit)).fetchall()
        return [dict(r) for r in rows]

# --- Memory Facts Operations ---

def add_memory_fact(topic: str, content: str) -> int:
    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO memory_facts (topic, content, timestamp)
            VALUES (?, ?, CURRENT_TIMESTAMP);
        """, (topic.strip(), content.strip()))
        conn.commit()
        return cursor.lastrowid

def get_memory_facts(topic: Optional[str] = None) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        if topic:
            rows = conn.execute("SELECT id, topic, content, timestamp FROM memory_facts WHERE topic LIKE ? ORDER BY id DESC;", (f"%{topic}%",)).fetchall()
        else:
            rows = conn.execute("SELECT id, topic, content, timestamp FROM memory_facts ORDER BY id DESC LIMIT 20;").fetchall()
        return [dict(r) for r in rows]

# --- Prompt Context Generator ---

def format_memory_summary_for_prompt() -> str:
    """Generates a concise markdown summary of preferences and learned facts for the Planner Agent."""
    try:
        init_db()
        prefs = get_all_preferences()
        facts = get_memory_facts()
        
        lines = []
        if prefs:
            lines.append("USER PREFERENCES:")
            for k, v in prefs.items():
                lines.append(f"- {k}: {v}")
                
        if facts:
            lines.append("\nSTORED FACTS & KNOWLEDGE:")
            for f in facts[:8]:
                lines.append(f"- [{f['topic']}]: {f['content']}")
                
        if lines:
            return "\n--- LONG-TERM MEMORY (PERSISTED) ---\n" + "\n".join(lines) + "\n-------------------------------------\n"
        return ""
    except Exception as e:
        print(f"Error generating memory summary: {e}")
        return ""

# Auto-initialize DB on import
init_db()
