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
        current_day = time.strftime('%d-%m-%Y', time.localtime())
        return os.path.join(self.directory, f"log_{current_day}.log")

    def ensure_log_directory(self):
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)

    def add_message(self, message):
        current_log_file = self.get_log_file()
        if self.log_file != current_log_file:
            self.log_file = current_log_file
        self.main.debug(message)
        with open(self.log_file, 'a') as file:
            file.write(f"{message}\n")