print("Starting...")
import time
import uuid

from yaml import safe_load
from dotenv import dotenv_values
import thingspeak

from hand_tracker import HandTracker
from server import Server
from logger import Logger
from database import Database

print("Imported classes")

"""
Initialize the variables as none, and only allow them to take their respective classes to avoid any issues.
"""
tracker: HandTracker | None = None
server: Server | None = None
logger: Logger | None = None
database: Database | None = None

config = None

class Main:

    thingspeak_keys: dict = {
        2791652: dotenv_values(".env")["MAIN_KEY"],
        2791860: dotenv_values(".env")["PERFORMANCE_KEY"]
    }

    def __init__(self):
        print("Initializing Main")
        global server, logger, database
        self.timers = {}
        logger = Logger(self)
        print("Logger initialized...")
        server = Server(self)
        print("Server initialized...")
        database = Database(self)
        print("Database initialized...")

    def read_config(self):
        """
        Read the content of the config YAML file and return it as a variable
        :return: The config's content.
        """
        try:
            with open("config.yml", "r") as config_file:
                global config
                config = safe_load(config_file)
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
            self.debug(f"No timer found with ID '{timer_id}'.")
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
            # Create HandTracker instance
            global tracker
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

        # Start hand tracking
        try:
            tracker.run()
        except Exception as e:
            print(f"An error occurred during hand tracking: {e}")

    def get_tracker(self):
        """
        Get the instance of the HandTracker class

        :return: HandTracker if initialized else None
        """
        return tracker

    def get_server(self):
        """
        Get instance of the Server class

        :return: Server if initialized else None
        """
        return server

    def get_logger(self):
        """
        Get instance of the Logger class

        :return: Logger if initialized, else None
        """
        return logger

    def get_config(self):
        """
        Get the variable storing the config]

        :return:
        """
        return config

    def get_database(self):
        """
        Get instance of the Database class

        :return: Database if initialized, else None
        """
        return database


    def add_message(self, message, timer_id=None, time_elapsed=None, date_time=None):
        """
        Adds a message to configured services

        :param message: Message to add
        :param timer_id: The timer's unique ID
        :param time_elapsed: The time elapsed between start of the action, and end.
        :param date_time: The current date and time.
        """
        if date_time is None:
            date_time = self.get_current_time()

        if self.read_config()["logs"]["log_to_logger"]:
            logger.add_message(message, date_time)
        if self.read_config()["logs"]["log_to_database"]:
            database.save_to_db(message, timer_id, time_elapsed, date_time)
        if self.read_config()["logs"]["log_to_thingspeak"]:
            state = None
            if("HIGH" in message):
                state = 0
            elif("LOW" in message):
                state = 1
            self.send_to_thingspeak(state, 2791652)

    def get_current_time(self):
        """
        Get the current date and time
        :return: The date and time as a string in the format 'YYYY-MM-DD HH:mm:ss'
        """
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

    def get_current_date(self):
        """
        Get the current date
        :return: The date as a string in the format 'YYYY-MM-DD'.
        """
        return time.strftime('%Y-%m-%d', time.localtime())

    def send_to_thingspeak(self, message, channel_id):
        """

        :param message: the message to send to ThingSpeak
        :param channel_id: The ThingSpeak channelID
        """
        channel = thingspeak.Channel(id=channel_id, api_key=self.thingspeak_keys[channel_id])
        if message is not None and self.read_config()["logs"]["log_to_thingspeak"]:
            try:
                channel.update({'field1': message})
                self.debug("Updated successfully: ")
            except Exception as e:
                self.add_message(f"[ERROR] {e}")

    def debug(self, message):
        """
        Debug method for testing purposes. Can be enabled or disabled in config.
        :param message: The message
        """
        if self.read_config()["debug"]:
            print(message)


if __name__ == "__main__":
    main = Main()
    main.run()
