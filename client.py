import socket
import threading
import os

from constants import (
    ACK,
    ALERT,
    BUFFER_SIZE,
    CLIENT_SERVER_HOST,
    REMOVED,
    SERVER_PORT,
    SUBSCRIBE,
    TIMEOUT,
)
from packet import parse_packet, create_packet
from ssl_config import encrypt_message


# Create UDP socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_socket.settimeout(TIMEOUT)

# Correct server address
server_address = (CLIENT_SERVER_HOST, SERVER_PORT)

received_sequences = set()
shutdown_event = threading.Event()


def subscribe():
    msg = encrypt_message(SUBSCRIBE)
    client_socket.sendto(msg.encode(), server_address)
    print("[INFO] Subscription request sent to server")


def leave_server():
    msg = encrypt_message("LEAVE")
    client_socket.sendto(msg.encode(), server_address)
    print("[INFO] Client leaving server")


def send_ack(seq):
    # create_packet → plain, so encrypt manually (IMPORTANT FIX)
    ack_packet = create_packet(seq, ACK, "RECEIVED")
    secure_packet = encrypt_message(ack_packet)
    client_socket.sendto(secure_packet.encode(), server_address)
    print(f"[ACK] Sent ACK for packet {seq}")


def shutdown_client(notify_server):
    if shutdown_event.is_set():
        return

    shutdown_event.set()

    if notify_server:
        try:
            leave_server()
        except OSError:
            pass

    try:
        client_socket.close()
    except OSError:
        pass


def handle_packet(seq, msg_type, payload, timestamp, priority):
    # Control packets should be handled immediately even if sequence numbers repeat.
    if msg_type == REMOVED:
        print("\n[INFO] You have been removed by server")
        print("[INFO] Closing client...")
        shutdown_event.set()
        try:
            client_socket.close()
        except OSError:
            pass
        os._exit(0)

    # Duplicate detection
    if seq in received_sequences:
        print(f"[DUPLICATE] Packet {seq} ignored")
        send_ack(seq)
        return

    received_sequences.add(seq)

    if msg_type == ALERT:
        print(f"[ALERT] {payload}")
        print(f"[INFO] Priority: {priority} | Timestamp: {timestamp}")
    else:
        print(f"[WARN] Unknown message type: {msg_type}")

    send_ack(seq)


def receive_messages():
    while not shutdown_event.is_set():
        try:
            data, _ = client_socket.recvfrom(BUFFER_SIZE)

            # ✅ FIX: decrypt + parse correctly
            seq, msg_type, payload, timestamp, priority = parse_packet(data.decode())

            handle_packet(seq, msg_type, payload, timestamp, priority)

        except socket.timeout:
            continue

        except OSError:
            if shutdown_event.is_set():
                break
            print("[ERROR] Socket closed unexpectedly")
            break

        except Exception as e:
            print("[ERROR]", e)


def user_input_listener():
    while not shutdown_event.is_set():
        try:
            cmd = input()
        except EOFError:
            shutdown_client(notify_server=True)
            break

        if cmd.strip().lower() == "exit":
            shutdown_client(notify_server=True)
            print("[INFO] Client closed")
            break


def start_client():
    print("----- UDP Notification Client -----")
    print(f"Connecting to server at {server_address[0]}:{server_address[1]}")
    print("Type 'exit' to leave server\n")

    subscribe()

    receiver_thread = threading.Thread(target=receive_messages, daemon=True)
    receiver_thread.start()

    user_input_listener()


if __name__ == "__main__":
    start_client()
