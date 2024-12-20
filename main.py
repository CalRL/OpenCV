import threading
import time
import yaml

from hand_tracker import HandTracker
from server import Server
from logger import Logger
from database import Database

tracker = None
server = None
logger = None
config = None
database = None


class Main:
    def __init__(self):
        global server, logger, database
        logger = Logger(self)
        server = Server(self)
        database = Database(self)

    def read_config(self):
        try:
            with open("config.yml", "r") as config_file:
                global config
                config = yaml.safe_load(config_file)
                return config
        except Exception as e:
            print("No config.yml file detected...")
            print("Creating now...")


    def run(self):
        """
        Main application entry point for hand tracking with optional WiFi connection
        """
        # Prompt user for connection preference
        while True:
            connect_choice = input("Do you want to connect to WiFi? (Y/N): ").strip().upper()

            if connect_choice == 'Y':
                # Create HandTracker instance with WiFi connection
                global tracker
                tracker = HandTracker(
                    self,
                    max_hands=1,
                    detection_confidence=0.7,
                    tracking_confidence=0.5
                )
                break
            elif connect_choice == 'N':
                # Create HandTracker instance without WiFi connection
                try:
                    tracker = HandTracker(
                        self,
                        max_hands=1,
                        detection_confidence=0.7,
                        tracking_confidence=0.5

                    )
                except Exception as e:
                    print(f"Error creating tracker: {e}")
                    print("Tracker may require a WiFi connection. Consider connecting.")
                    continue
                break
            else:
                print("Invalid input. Please enter Y or N.")
                exit()

        # Start hand tracking
        try:
            tracker.run()
        except Exception as e:
            print(f"An error occurred during hand tracking: {e}")

    def get_tracker(self):
        return tracker

    def get_server(self):
        return server

    def get_logger(self):
        return logger

    def get_config(self):
        return config

    def get_database(self):
        return database

    def add_message(self, message):
        if self.read_config()["logs"]["log_to_logger"]:
            logger.add_message(message)
        if self.read_config()["logs"]["log_to_database"]:
            database.save_to_db(message)

    def get_current_time(self):
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

if __name__ == "__main__":

    main = Main()
    main.run()




