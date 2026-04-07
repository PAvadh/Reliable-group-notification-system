from ssl_config import decrypt_message, encrypt_message

import time


def serialize_plain_packet(seq, msg_type, data):
    return f"{seq}|{msg_type}|{data}"


def parse_plain_packet(packet):
    parts = packet.split("|")

    seq = int(parts[0])
    msg_type = parts[1]
    timestamp = int(parts[2])
    priority = parts[3]
    message = parts[4]

    return seq, msg_type, message, timestamp, priority


def create_packet(seq, msg_type, message, priority="NORMAL"):
    timestamp = int(time.time())
    return f"{seq}|{msg_type}|{timestamp}|{priority}|{message}"

def parse_packet(packet):
    decrypted_packet = decrypt_message(packet)
    return parse_plain_packet(decrypted_packet)
