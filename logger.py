import time
import os

class Logger:
    def __init__(self):
        self.log_file = self.get_log_file()
        self.ensure_log_directory()

    def get_log_file(self):
        current_day = time.strftime('%d-%m-%Y', time.localtime())
        return os.path.join('logs', f"log_{current_day}.log")

    def ensure_log_directory(self):
        if not os.path.exists('logs'):
            os.makedirs('logs')

    def add_message(self, message):
        current_log_file = self.get_log_file()
        if self.log_file != current_log_file:
            self.log_file = current_log_file
        print(message)
        with open(self.log_file, 'a') as file:
            file.write(f"{message}\n")

    def get_last_messages(self, number):
        """
        Reads the last 'n' messages from the current log file.
        :param number: Number of messages to retrieve.
        :return: List of last 'n' messages.
        """
        try:
            with open(self.log_file, 'r') as file:
                lines = file.readlines()
                return lines[-number:]  # Get the last 'n' lines
        except FileNotFoundError:
            return []