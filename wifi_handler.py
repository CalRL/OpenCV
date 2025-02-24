import socket
from server import Server

client_handler = None
class WiFiClientHandler:
    def __init__(self, main):
        """
        Initializes the WiFi client with the given host and port.
        """
        print(f"{WiFiClientHandler.__name__} Fetching config...")
        self.config = main.get_config()
        self.host: str = self.config['arduino']["host"]
        self.port: int = self.config['arduino']["port"]
        print(f"Connecting to {self.host}:{self.port}")
        self.client_socket = None
        self.server = main.get_server()
        self.server.run()
        self.logger = main.get_logger()
        print(f"{WiFiClientHandler.__name__} Init complete")
        self.main = main

        global client_handler
        client_handler = self

    def create_socket(self):
        return socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        """
        Connects to the Arduino.
        """
        try:
            self.client_socket = self.create_socket()
            self.client_socket.connect((self.host, self.port))
            print(f"Connected to Arduino Wi-Fi server at {self.host}:{self.port}")
        except Exception as e:
            print(f"Error connecting to the server: {e}")
            i = 1
            while i < 10:
                print(f"Retrying {10-i} more times...")
                self.client_socket.connect((self.host, self.port))
                i += 1
            if not self.client_socket:
                exit()

    def send_message(self, message):
        """
        Sends a message to the Arduino server.

        :param message: String message to send
        """
        if not self.client_socket:
            print("Not connected to the server. Trying now...")
            self.client_socket.connect(self.host, self.port)
            return

        try:
            # Add newline to indicate end of message
            self.client_socket.sendall((message.strip() + '\n').encode())
            print(f"Sent: {message}")
        except Exception as e:
            print(f"Error sending message: {e}")

    def receive_message(self):
        """
        Receives a message from the Arduino server.

        :return: The received message as a string
        """
        if not self.client_socket:
            print("Not connected to the server. Call connect() first.")
            i = 1
            while i < 10:
                print(f"Retrying {10-i} more times...")
                self.client_socket.connect()
                i += 1
            if not self.client_socket:
                exit()

        try:
            response = self.client_socket.recv(1024).decode().strip()
            if response != " " and response != "":
                self.main.add_message(response)
                self.main.debug(f"SERVER: Received from Arduino: {response}")
            return response
        except Exception as e:
            print(f"Error receiving message: {e}")
            return None

    def disconnect(self):
        """
        Closes the connection to the Arduino server.
        """
        if self.client_socket:
            try:
                self.client_socket.close()
                print("Disconnected from the Arduino server.")
            except Exception as e:
                print(f"Error closing the connection: {e}")
        self.client_socket = None


def send_message(message):
    """
    Static method to send a message to the arduino.
    :param message: The message to send.
    """
    if client_handler is not None:
        client_handler.send_message(message)
    else:
        print("Cannot send message, client_handler is None.")
