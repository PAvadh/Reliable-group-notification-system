import socket
import threading

from constants import ACK, ALERT, BUFFER_SIZE, CLIENT_SERVER_HOST, SERVER_PORT, SUBSCRIBE, TIMEOUT
from packet import create_packet, parse_packet
from ssl_config import encrypt_message


client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_socket.settimeout(TIMEOUT)
server_address = (CLIENT_SERVER_HOST, SERVER_PORT)

received_sequences = set()
shutdown_event = threading.Event()


def subscribe():
    client_socket.sendto(encrypt_message(SUBSCRIBE).encode(), server_address)
    print("[INFO] Subscription request sent to server")


def leave_server():
    client_socket.sendto(encrypt_message("LEAVE").encode(), server_address)
    print("[INFO] Client leaving server")


def send_ack(seq):
    ack_packet = create_packet(seq, ACK, "RECEIVED")
    client_socket.sendto(ack_packet.encode(), server_address)
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


def handle_packet(seq, msg_type, payload):
    # If a duplicate arrives, ACK it and skip duplicate display.
    if seq in received_sequences:
        send_ack(seq)
        return

    received_sequences.add(seq)

    if msg_type == ALERT:
        print(f"[ALERT] {payload}")
    else:
        print(f"[WARN] Unsupported server message type: {msg_type}")

    send_ack(seq)


def receive_messages():
    while not shutdown_event.is_set():
        try:
            data, _ = client_socket.recvfrom(BUFFER_SIZE)
            seq, msg_type, payload = parse_packet(data.decode())
            handle_packet(seq, msg_type, payload)

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
