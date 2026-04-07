import socket
import threading
import random
import time

from constants import ACK, ALERT, BUFFER_SIZE, REMOVED, SERVER_HOST, SERVER_PORT, SUBSCRIBE, TIMEOUT
from packet import create_packet, parse_plain_packet
from ssl_config import decrypt_message, encrypt_message

#PROBABILITIES
LOSS_PROB = 0.25
DUP_PROB = 0.15
DELAY_PROB = 0.20

#CLIENT MANAGEMENT
clients = {}
client_counter = 1
subscribers = set()

sequence_number = 1
acks_received = {}
packets_by_sequence = {}

server_socket = None
server_lock = threading.Lock()
shutdown_event = threading.Event()


# ================== SEND PACKET ==================
def send_packet(packet, client):

    client_id = clients.get(client, {}).get("id", "Unknown")

    # LOSS
    if random.random() < LOSS_PROB:
        print(f"[SIM] Packet LOST for ({client[0]}, {client[1]}, {client_id})")
        return

    # DELAY
    if random.random() < DELAY_PROB:
        delay = random.uniform(0.5, 2)
        print(f"[SIM] Packet DELAY {delay:.2f}s for ({client[0]}, {client[1]}, {client_id})")
        time.sleep(delay)

    secure_packet = encrypt_message(packet)
    server_socket.sendto(secure_packet.encode(), client)

    # DUPLICATE
    if random.random() < DUP_PROB:
        print(f"[SIM] DUPLICATE packet sent to ({client[0]}, {client[1]}, {client_id})")
        server_socket.sendto(secure_packet.encode(), client)


# ================== SHOW CLIENT ==================
def show_clients():
    with server_lock:
        if not clients:
            print("[INFO] No active clients")
            return

        print("\n[CLIENT LIST]")
        for addr, data in clients.items():
            print(f"{data['id']} -> ({addr[0]}, {addr[1]})")
        print(f"Total clients: {len(clients)}\n")


def remove_client_by_id(client_id):
    with server_lock:
        for addr, data in list(clients.items()):
            if data["id"].lower() == client_id.lower():
                try:
                    removal_msg = create_packet(0, REMOVED, "You have been removed by server")
                    secure_packet = encrypt_message(removal_msg)
                    server_socket.sendto(secure_packet.encode(), addr)
                except Exception as e:
                    print("[ERROR sending removal msg]", e)

                subscribers.discard(addr)
                del clients[addr]

                # Remove stale ACK references so wait/retransmit logic stays consistent
                for acked_clients in acks_received.values():
                    acked_clients.discard(addr)

                print(f"[REMOVE] {data['id']} removed by server")
                return

        print(f"[ERROR] Client {client_id} not found")


# ================== HANDLE CLIENT ==================
def handle_client_messages():
    global client_counter

    while not shutdown_event.is_set():
        try:
            data, addr = server_socket.recvfrom(BUFFER_SIZE)
        except socket.timeout:
            continue
        except OSError as e:
            if shutdown_event.is_set():
                break
            print(f"[WARN] Socket receive error: {e}")
            continue

        try:
            message = decrypt_message(data.decode())

            # SUBSCRIBE
            if message == SUBSCRIBE:
                with server_lock:
                    if addr not in subscribers:
                        subscribers.add(addr)

                        client_id = f"Client-{client_counter}"
                        client_counter += 1

                        clients[addr] = {
                            "id": client_id,
                            "last_seen": time.time()
                        }

                        print(f"[JOIN] {client_id} joined from ({addr[0]}, {addr[1]})")

                        print("[SYNC] Existing clients:")
                        for addr_existing, data in clients.items():
                            if addr_existing != addr:
                                print(f"   {data['id']} -> ({addr_existing[0]}, {addr_existing[1]})")
                continue

            # LEAVE
            if message == "LEAVE":
                with server_lock:
                    if addr in subscribers:
                        subscribers.remove(addr)

                    if addr in clients:
                        print(f"[INFO] {clients[addr]['id']} left")
                        del clients[addr]
                continue

            # ACK
            seq, msg_type, _, _, _ = parse_plain_packet(message)

            if msg_type == ACK:
                with server_lock:
                    if seq not in acks_received:
                        acks_received[seq] = set()

                    if addr not in acks_received[seq]:
                        acks_received[seq].add(addr)

                        client_id = clients.get(addr, {}).get("id", addr)
                        print(f"\n[ACK] Packet {seq} acknowledged by {client_id}")

        except Exception as e:
            print("[ERROR]", e)


# ================== SEND ONE PACKET ==================
def broadcast_alert(message):
    global sequence_number

    with server_lock:
        active_clients = list(subscribers)

    if not active_clients:
        print("[INFO] No clients connected")
        return

    seq = sequence_number
    packet = create_packet(seq, ALERT, message)

    packets_by_sequence[seq] = packet
    acks_received[seq] = set()

    print(f"[SEND] Broadcasting alert #{seq}")

    for client in active_clients:
        send_packet(packet, client)

    wait_for_ack(seq)
    sequence_number += 1


# ================== WAIT FOR ACK ==================
def wait_for_ack(seq):
    start = time.time()

    while True:
        with server_lock:
            total = len(subscribers)
            acked = len(acks_received.get(seq, []))

        if acked == total:
            print(f"[SUCCESS] All clients acknowledged packet {seq}")
            return

        if time.time() - start > TIMEOUT:
            print(f"[TIMEOUT] Retransmitting packet {seq}")

            packet = packets_by_sequence[seq]

            for client in subscribers:
                if client not in acks_received[seq]:
                    send_packet(packet, client)

            start = time.time()


# ================== INPUT LOOP ==================
def alert_input_loop():
    global sequence_number

    while not shutdown_event.is_set():
        msg = input("\nEnter alert message: ")

        # SHOW CLIENT
        if msg.strip().upper() == "SHOW CLIENT":
            show_clients()
            continue

        # REMOVE CLIENT
        if msg.strip().upper().startswith("REMOVE CLIENT"):
            parts = msg.strip().split(maxsplit=2)
            if len(parts) < 3 or not parts[2].strip():
                print("[ERROR] Use format: REMOVE CLIENT <client-id>")
            else:
                remove_client_by_id(parts[2])
            continue

        # CUSTOM PACKET
        if "|" in msg:
            try:
                parts = msg.split("|", 3)

                seq = int(parts[0])
                msg_type = parts[1]
                priority = parts[2]
                message = parts[3]

                packet = create_packet(seq, msg_type, message, priority)

                print(f"[CUSTOM PACKET] {packet}")

                packets_by_sequence[seq] = packet
                acks_received[seq] = set()

                for client in subscribers:
                    send_packet(packet, client)

                wait_for_ack(seq)

                # FIX SEQUENCE
                sequence_number = max(sequence_number, seq + 1)

            except Exception:
                print("[ERROR] Use format: seq|type|priority|message")

            continue

        # EXIT
        if msg.lower() == "exit":
            shutdown_event.set()
            break

        # NORMAL MESSAGE
        if msg.strip():
            broadcast_alert(msg) 


# ================== START SERVER ==================
def start_server():
    global server_socket

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.settimeout(1.0)
    server_socket.bind((SERVER_HOST, SERVER_PORT))

    print("----- UDP Notification Server Started -----")
    print(f"Listening on {SERVER_HOST}:{SERVER_PORT}")

    thread = threading.Thread(target=handle_client_messages, daemon=True)
    thread.start()

    try:
        alert_input_loop()
    finally:
        shutdown_event.set()
        server_socket.close()


if __name__ == "__main__":
    start_server()
