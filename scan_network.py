import socket
import ipaddress

def scan_network(network):
    print(f"Scanning network: {network}")
    for ip in ipaddress.IPv4Network(network, strict=False):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                s.connect((str(ip), 80))  # Port 80 for HTTP (or change based on your Arduino server's port)
                print(f"Device found: {ip}")
        except:
            pass

if __name__ == '__main__':
    # Replace with your local network range (e.g., '192.168.1.0/24')
    scan_network('192.168.0.1/24')
