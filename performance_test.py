import statistics
import time

import client
from constants import ALERT
from packet import create_packet, parse_packet
from ssl_config import decrypt_message, encrypt_message


ITERATIONS = 300
WARMUP_ITERATIONS = 20


def benchmark(name, func, iterations=ITERATIONS, warmup=WARMUP_ITERATIONS):
    for _ in range(warmup):
        func()

    durations = []
    start = time.perf_counter()
    for _ in range(iterations):
        t0 = time.perf_counter()
        func()
        durations.append(time.perf_counter() - t0)

    total = time.perf_counter() - start
    print(f"{name}:")
    print(f"  iterations : {iterations}")
    print(f"  average    : {statistics.mean(durations) * 1000:.3f} ms")
    print(f"  median     : {statistics.median(durations) * 1000:.3f} ms")
    print(f"  throughput : {iterations / total:.2f} ops/sec")
    print()


def benchmark_secure_message_round_trip():
    sample = "ALERT|Emergency notification payload for performance testing"
    benchmark("Secure message round-trip", lambda: decrypt_message(encrypt_message(sample)), 20, 2)


def benchmark_packet_round_trip():
    def run():
        packet = create_packet(25, ALERT, "Packet payload used for end-to-end parsing")
        parse_packet(packet)

    benchmark("Encrypted packet create/parse", run, 20, 2)


def benchmark_small_control_message():
    benchmark("Control message crypto", lambda: decrypt_message(encrypt_message("SUB")), 20, 2)


def reset_client_state():
    client.received_sequences.clear()


def benchmark_client_normal_handling():
    reset_client_state()
    original_send_ack = client.send_ack
    original_print = client.__dict__.get("print", print)

    acked = []

    def fake_send_ack(seq):
        acked.append(seq)

    client.send_ack = fake_send_ack
    client.print = lambda *args, **kwargs: None

    try:
        def run():
            reset_client_state()
            acked.clear()

            for seq in range(1, 201):
                client.handle_packet(seq, ALERT, "ordered payload")

            if len(acked) != 200:
                raise AssertionError("Client did not ACK all packets")

        benchmark("Client normal packet handling (200 packets)", run, 300, 20)
    finally:
        client.send_ack = original_send_ack
        client.print = original_print


def main():
    print("UDP Notification System Performance Tests")
    print("----------------------------------------")
    print()
    benchmark_secure_message_round_trip()
    benchmark_small_control_message()
    benchmark_packet_round_trip()
    benchmark_client_normal_handling()


if __name__ == "__main__":
    try:
        main()
    finally:
        client.shutdown_event.set()
        client.client_socket.close()
