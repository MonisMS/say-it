import sqlite3
import os
from datetime import datetime


class History:
    def __init__(self):
        app_dir = os.path.join(
            os.environ.get("APPDATA", os.path.expanduser("~")), "say-it"
        )
        os.makedirs(app_dir, exist_ok=True)
        db_path = os.path.join(app_dir, "history.db")
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._create_table()

    def _create_table(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                text      TEXT    NOT NULL,
                timestamp TEXT    NOT NULL
            )
        """)
        self.conn.commit()

    def add(self, text: str):
        self.conn.execute(
            "INSERT INTO history (text, timestamp) VALUES (?, ?)",
            (text, datetime.now().isoformat()),
        )
        self.conn.commit()

    def recent(self, limit: int = 20):
        cursor = self.conn.execute(
            "SELECT id, text, timestamp FROM history ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        return cursor.fetchall()

    def show(self):
        rows = self.recent()
        if not rows:
            print("No history yet.")
            return
        print("\n--- Recent transcriptions ---")
        for row in rows:
            print(f"[{row[2][:19]}]  {row[1]}")
        print("-----------------------------\n")
