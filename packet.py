from ssl_config import decrypt_message, encrypt_message


def serialize_plain_packet(seq, msg_type, data):
    return f"{seq}|{msg_type}|{data}"


def parse_plain_packet(packet):
    parts = packet.split("|", 2)
    if len(parts) != 3:
        raise ValueError("Invalid packet format")

    seq = int(parts[0])
    msg_type = parts[1]
    data = parts[2]
    return seq, msg_type, data


def create_packet(seq, msg_type, data):
    raw_packet = serialize_plain_packet(seq, msg_type, data)
    return encrypt_message(raw_packet)


def parse_packet(packet):
    decrypted_packet = decrypt_message(packet)
    return parse_plain_packet(decrypted_packet)
