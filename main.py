import threading
import time
import uuid

import yaml
from dotenv import dotenv_values
import thingspeak

import wifi_handler
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

    thingspeak_keys = {
        2791652: dotenv_values(".env")["MAIN_KEY"],
        2791860: dotenv_values(".env")["PERFORMANCE_KEY"]
    }

    def __init__(self):
        global server, logger, database
        self.timers = {}
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

    def start_timer(self):
        """
        Starts a timer and generates a unique, non-duplicate timer ID.
        :return: The unique timer ID
        """
        while True:
            # Generate a unique ID
            timer_id = str(uuid.uuid4())
            if timer_id not in self.timers:
                break

        # Start the timer
        self.timers[timer_id] = time.time()
        self.debug(f"Started timer with ID '{timer_id}'.")
        return timer_id

    def stop_timer(self, timer_id):
        """
        Stops a timer with the given ID and returns the elapsed time.
        :param timer_id: Unique ID for the timer
        :return: Elapsed time in seconds, or None if the timer doesn't exist
        """
        if timer_id not in self.timers:
            print(f"No timer found with ID '{timer_id}'.")
            return None
        else:
            elapsed_time = time.time() - self.timers[timer_id]
            del self.timers[timer_id]  # Remove the timer from the dictionary
            self.debug(f"Stopped timer with ID '{timer_id}'. Elapsed time: {elapsed_time:.3f} seconds")
            self.send_to_thingspeak(elapsed_time, 2791860)
            return elapsed_time

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
        if self.read_config()["logs"]["log_to_thingspeak"]:
            state = None
            if("HIGH" in message):
                state = 1
            elif("LOW" in message):
                state = 0
            self.send_to_thingspeak(state, 2791652)

    def get_current_time(self):
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

    def send_to_thingspeak(self, message, channel_id):
        channel = thingspeak.Channel(id=channel_id, api_key=self.thingspeak_keys[channel_id])
        if message is not None and self.read_config()["logs"]["log_to_thingspeak"]:
            try:
                channel.update({'field1': message})
                self.debug("Updated successfully: ")
            except Exception as e:
                self.add_message(f"[ERROR] {e}")

    def debug(self, message):
        if self.read_config()["debug"]:
            print(message)




if __name__ == "__main__":
    main = Main()
    main.run()
