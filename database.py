import time
import threading
import sqlite3


class Database:
    def __init__(self, main):
        self.server = main.get_server()
        self.logger = main.get_logger()
        self.config = main.get_config()
        self.main = main
        try:
            conn = sqlite3.connect(self.config["database"]["path"])
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS light_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    string TEXT NOT NULL
            """)
            conn.commit()
            conn.close()
            message = "Database created"
            self.main.add_message(message)

        except Exception as e:
            message = f"[ERROR] {e}"
            self.main.add_message(message)

    def save_to_db(self, message):
        try:
            conn = sqlite3.connect(self.config["database"]["path"])
            cursor = conn.cursor()
            cursor.execute("""
                    INSERT INTO light_logs (timestamp, string)
                    VALUES (datetime('now'), ?, ?)
                """, (message))
            conn.commit()
            conn.close()
        except Exception as e:
            message = f"[ERROR] Couldn't save string: {e}"
            self.main.add_message(message)

