import time
import os


class Logger:
    def __init__(self, main):
        self.config = main.read_config()
        self.directory: str = self.config['logs']['directory']
        self.log_file = self.get_log_file()
        self.ensure_log_directory()
        self.main = main

    def get_log_file(self):
        """
        Retrives the log file
        :return: The log file
        """
        current_day = time.strftime('%d-%m-%Y', time.localtime())
        return os.path.join(self.directory, f"log_{current_day}.log")

    def ensure_log_directory(self):
        """
        Check if log file exists, if the log file doesn't exist, create it.
        """
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)

    def add_message(self, message, date_time=None):
        """
        Adds a message to the log file.
        Will also print to console if debug is enabled.
        :param message: The message to added.
        :param date_time: The current date and time.
        """
        log_message = f"{date_time}: {message}"
        current_log_file = self.get_log_file()
        if self.log_file != current_log_file:
            self.log_file = current_log_file
        self.main.debug(f"Adding to log file: {log_message}")
        with open(self.log_file, 'a') as file:
            file.write(f"{log_message}\n")