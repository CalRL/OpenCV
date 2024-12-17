import threading
import time

from hand_tracker import HandTracker
from server import Server
from logger import Logger

tracker = None
server = None
logger = None
class Main:
    def __init__(self):
        global server, logger, tracker
        logger = Logger()
        server = Server(self)

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
                    host="192.168.4.1",
                    port=80,
                    max_hands=1,
                    detection_confidence=0.7,
                    tracking_confidence=0.5
                )
                break
            elif connect_choice == 'N':
                # Create HandTracker instance without WiFi connection
                # Note: You might need to modify the WiFiClientHandler to support a no-connect mode
                try:
                    tracker = HandTracker(
                        self,
                        host=None,
                        port=None,
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


if __name__ == "__main__":

    main = Main()
    main.run()



