import os


SERVER_HOST = os.getenv("UDP_SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("UDP_SERVER_PORT", "5000"))
CLIENT_SERVER_HOST = os.getenv("UDP_CLIENT_SERVER_HOST", "127.0.0.1")

BUFFER_SIZE = 1024
TIMEOUT = float(os.getenv("UDP_TIMEOUT", "2"))

# Message types
SUBSCRIBE = "SUB"
ALERT = "ALERT"
ACK = "ACK"
