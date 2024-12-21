import os
import time
import threading
import sqlite3


class Database:
    def __init__(self, main):
        self.server = main.get_server()
        self.logger = main.get_logger()
        self.config = main.get_config()
        self.main = main

        # Create the db if it doesnt exist already
        db_path: str = self.config['database']['path']
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # Connect and create the table if it doesnt exist already
        try:
            print(f"Trying db at {db_path}")
            conn = sqlite3.connect(self.config["database"]["path"])
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS light_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    string TEXT NOT NULL,
                    timer_id TEXT,
                    time FLOAT
                    )
            """)
            conn.commit()
            conn.close()
            message = "Database created"
            self.logger.add_message(message)

        except Exception as e:
            message = f"[ERROR] {e}"
            print(message)
            self.logger.add_message(message)

    def save_to_db(self, message, timer_id, time):
        try:
            conn = sqlite3.connect(self.config["database"]["path"])
            cursor = conn.cursor()
            cursor.execute("""
                    INSERT INTO light_logs (timestamp, string, timer_id, time)
                    VALUES (?, ?, ?, ?)
                """, (self.main.get_current_time(), message, timer_id, time))
            conn.commit()
            conn.close()
            self.main.debug("Saved successfully.")
        except Exception as e:
            message = f"[ERROR] Couldn't save string: {e}"
            print(message)
            self.logger.add_message(message)

