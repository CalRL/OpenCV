import socket
import time
from server import Server


class WiFiClientHandler:
    def __init__(self, host, port, main):
        """
        Initializes the WiFi client with the given host and port.

        :param host: IP address of the Arduino server
        :param port: Port number of the Arduino server
        """
        self.host = host
        self.port = port
        self.client_socket = None
        self.server = main.get_server()
        self.server.run()

    def connect(self):
        """
        Connects to the Arduino Wi-Fi server.
        """
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.host, self.port))
            print(f"Connected to Arduino Wi-Fi server at {self.host}:{self.port}")
        except Exception as e:
            print(f"Error connecting to the server: {e}")
            self.client_socket = None

    def send_message(self, message):
        """
        Sends a message to the Arduino server.

        :param message: String message to send
        """
        if not self.client_socket:
            print("Not connected to the server. Call connect() first.")
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
            exit()

        try:
            response = self.client_socket.recv(1024).decode().strip()
            if response != " " and response != "":
                self.server.add_message(response)
                print(f"Received from Arduino: {response}")
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


if __name__ == "__main__":
    # Update with your Arduino server's IP and port
    host = "192.168.4.1"
    port = 80

    client = WiFiClientHandler(host, port)
    client.connect()

    try:
        while True:
            msg = input("Enter a message to send (type 'exit' to quit): ")
            if msg.lower() == "exit":
                break
            client.send_message(msg)
            client.receive_message()
            time.sleep(0.1)
    finally:
        client.disconnect()
