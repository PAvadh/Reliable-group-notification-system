import socket
import threading
import time

from constants import ACK, ALERT, BUFFER_SIZE, SERVER_HOST, SERVER_PORT, SUBSCRIBE, TIMEOUT
from packet import create_packet, parse_plain_packet
from ssl_config import decrypt_message


subscribers = set()
sequence_number = 1
acks_received = {}
targets_by_sequence = {}

server_socket = None
server_lock = threading.Lock()
shutdown_event = threading.Event()


def remove_subscriber(addr, reason):
    with server_lock:
        if addr in subscribers:
            subscribers.remove(addr)
            print(f"[INFO] Client removed ({reason}): {addr}")


def send_packet(packet, client):
    server_socket.sendto(packet.encode(), client)


def handle_client_messages():
    while not shutdown_event.is_set():
        try:
            data, addr = server_socket.recvfrom(BUFFER_SIZE)
        except socket.timeout:
            continue
        except OSError:
            if shutdown_event.is_set():
                break
            raise

        try:
            message = decrypt_message(data.decode())

            if message == SUBSCRIBE:
                with server_lock:
                    is_new = addr not in subscribers
                    subscribers.add(addr)
                if is_new:
                    print("[INFO] Client subscribed:", addr)
                continue

            if message == "LEAVE":
                remove_subscriber(addr, "client leave")
                continue

            seq, msg_type, _ = parse_plain_packet(message)
            if msg_type == ACK:
                with server_lock:
                    ack_set = acks_received.setdefault(seq, set())
                    if addr not in ack_set:
                        ack_set.add(addr)
                        print(f"[ACK] Packet {seq} acknowledged by {addr}")
            else:
                print(f"[WARN] Unsupported client message type: {msg_type}")

        except Exception as e:
            print("[ERROR]", e)


def wait_for_ack(seq):
    with server_lock:
        expected_clients = set(targets_by_sequence.get(seq, set()))

    start = time.time()
    while True:
        with server_lock:
            acked_clients = set(acks_received.get(seq, set()))

        if expected_clients.issubset(acked_clients):
            print(f"[SUCCESS] All clients acknowledged packet {seq}")
            return

        if time.time() - start >= TIMEOUT:
            missing = expected_clients - acked_clients
            if missing:
                print(f"[TIMEOUT] Missing ACKs for packet {seq}: {sorted(missing)}")
            else:
                print(f"[SUCCESS] All clients acknowledged packet {seq}")
            return

        time.sleep(0.05)


def broadcast_alert(message):
    global sequence_number

    with server_lock:
        active_subscribers = list(subscribers)

    if not active_subscribers:
        print("[INFO] No subscribers available")
        return

    seq = sequence_number
    packet = create_packet(seq, ALERT, message)

    with server_lock:
        acks_received[seq] = set()
        targets_by_sequence[seq] = set(active_subscribers)

    print(f"[SEND] Broadcasting alert #{seq}")
    for client in active_subscribers:
        send_packet(packet, client)

    wait_for_ack(seq)
    sequence_number += 1


def alert_input_loop():
    while not shutdown_event.is_set():
        try:
            message = input("Enter alert message: ")
        except EOFError:
            shutdown_event.set()
            break

        if message.strip().lower() == "exit":
            shutdown_event.set()
            break

        if not message.strip():
            continue

        broadcast_alert(message)


def start_server():
    global server_socket

    shutdown_event.clear()
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.settimeout(1.0)
    server_socket.bind((SERVER_HOST, SERVER_PORT))

    print("----- UDP Notification Server Started -----")
    print(f"Listening on {SERVER_HOST}:{SERVER_PORT}")
    print("Use UDP_CLIENT_SERVER_HOST on each client device to point at this server")
    print("Type 'exit' to stop the server")

    listener_thread = threading.Thread(target=handle_client_messages, daemon=True)
    listener_thread.start()

    try:
        alert_input_loop()
    finally:
        shutdown_event.set()
        try:
            server_socket.close()
        except OSError:
            pass


if __name__ == "__main__":
    start_server()
