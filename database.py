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
                    string TEXT NOT NULL
                    )
            """)
            conn.commit()
            conn.close()
            message = "Database created"
            self.logger.add_message(message)

        except Exception as e:
            message = f"[ERROR] {e}"
            self.logger.add_message(message)

    def save_to_db(self, message):
        try:
            conn = sqlite3.connect(self.config["database"]["path"])
            cursor = conn.cursor()
            cursor.execute("""
                    INSERT INTO light_logs (timestamp, string)
                    VALUES (?, ?)
                """, (self.main.get_current_time(), message))
            conn.commit()
            conn.close()
            print("Saved successfully.")
        except Exception as e:
            message = f"[ERROR] Couldn't save string: {e}"
            self.main.add_message(message)

