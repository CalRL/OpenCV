import socket
from server import Server
def send_message_to_server(message, host='127.0.0.1', port=5000):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((host, port))
            client_socket.sendall(message.encode('utf-8'))
            print(f"Message sent: {message}")
    except ConnectionRefusedError:
        print("Could not connect to the server. Ensure the server is running and accessible.")

if __name__ == '__main__':
    while True:
        message = input("Enter a message to send to the server (type 'exit' to quit): ")
        if message.lower() == 'exit':
            break
        send_message_to_server(message)
