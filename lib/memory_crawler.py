__version__ = "3.2.0"

import sqlite3
import json
import os
import urllib.request
import urllib.error
from datetime import datetime
from typing import Optional


DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "fts5_index.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = _get_conn()
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS sessions_fts USING fts5(
            session_id,
            timestamp,
            role,
            content,
            token_count
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions_meta (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE,
            timestamp TEXT,
            file_path TEXT
        )
    """)
    conn.commit()
    conn.close()


def index_session(path: str) -> dict:
    init_db()
    conn = _get_conn()
    cursor = conn.cursor()

    session_id = os.path.splitext(os.path.basename(path))[0]
    timestamp = datetime.now().isoformat()

    cursor.execute(
        "INSERT OR REPLACE INTO sessions_meta (session_id, timestamp, file_path) VALUES (?, ?, ?)",
        (session_id, timestamp, path),
    )

    indexed_count = 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                role = entry.get("role", "unknown")
                content = entry.get("content", "")
                token_count = entry.get("token_count", 0)

                cursor.execute(
                    "INSERT INTO sessions_fts (session_id, timestamp, role, content, token_count) VALUES (?, ?, ?, ?, ?)",
                    (session_id, timestamp, role, content, token_count),
                )
                indexed_count += 1
            except json.JSONDecodeError:
                continue

    conn.commit()
    conn.close()

    return {
        "session_id": session_id,
        "indexed_entries": indexed_count,
        "timestamp": timestamp,
    }


def search_hybrid(query: str, limit: int = 10) -> dict:
    init_db()
    conn = _get_conn()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT session_id, timestamp, role, content, token_count,
               bm25(sessions_fts) as rank
        FROM sessions_fts
        WHERE sessions_fts MATCH ?
        ORDER BY rank
        LIMIT ?
    """,
        (query, limit),
    )

    rows = cursor.fetchall()
    conn.close()

    results = []
    for row in rows:
        results.append(
            {
                "session_id": row[0],
                "timestamp": row[1],
                "role": row[2],
                "content": row[3],
                "token_count": row[4],
                "rank": row[5],
            }
        )

    llm_summary = _generate_summary(query, results) if results else None

    return {
        "query": query,
        "matches": results,
        "total_matches": len(results),
        "llm_summary": llm_summary,
    }


def _generate_summary(query: str, results: list) -> str:
    if not results:
        return "No relevant results found."

    content_snippets = [r["content"][:500] for r in results[:3]]
    combined = "\n".join(content_snippets)

    prompt = (
        f"You are a search summary assistant. Based on the following search results for "
        f"query '{query}', provide a concise 2-sentence summary of the most relevant findings.\n\n"
        f"Search results:\n{combined}\n\nSummary:"
    )

    payload = json.dumps(
        {"model": "qwen2.5:7b", "prompt": prompt, "stream": False}
    ).encode("utf-8")

    try:
        req = urllib.request.Request(
            "http://localhost:11434/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result.get("response", "").strip()
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
        fallback = (
            f"Hybrid search for '{query}' found {len(results)} matches. "
            f"Top results mention: {combined[:150]}..."
        )
        return fallback


def get_stats() -> dict:
    init_db()
    conn = _get_conn()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM sessions_fts")
    total_entries = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT session_id) FROM sessions_meta")
    total_sessions = cursor.fetchone()[0]

    conn.close()

    return {
        "total_entries": total_entries,
        "total_sessions": total_sessions,
        "db_path": DB_PATH,
    }
