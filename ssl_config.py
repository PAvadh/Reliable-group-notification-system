import base64
import hashlib
import hmac
import os
import secrets
from functools import lru_cache


SECURE_PACKET_VERSION = "UDPSEC1"
PBKDF2_SALT = b"cn-project-udp-demo-v1"
PBKDF2_ROUNDS = 200_000
NONCE_SIZE = 16
MAC_SIZE = 32
INSECURE_DEFAULT_SECRET = "change-this-shared-secret"


def _resolve_shared_secret(shared_secret):
    """
    Resolve secret key and enforce explicit configuration.
    """
    resolved_secret = shared_secret
    if resolved_secret is None:
        resolved_secret = os.getenv("UDP_SHARED_SECRET", "").strip()

    if not resolved_secret or resolved_secret == INSECURE_DEFAULT_SECRET:
        raise ValueError(
            "UDP_SHARED_SECRET is required and must not use the insecure default value."
        )

    return resolved_secret


@lru_cache(maxsize=8)
def _derive_keys(shared_secret):
    """
    Derive independent encryption and authentication keys from one secret
    """
    key_material = hashlib.pbkdf2_hmac(
        "sha256",
        shared_secret.encode("utf-8"),
        PBKDF2_SALT,
        PBKDF2_ROUNDS,
        dklen=64,
    )
    return key_material[:32], key_material[32:]


def _build_keystream(encryption_key, nonce, length):
    """
    Generate a deterministic byte stream for XOR encryption
    """
    output = bytearray()
    counter = 0

    while len(output) < length:
        counter_bytes = counter.to_bytes(4, "big")
        block = hmac.new(
            encryption_key,
            nonce + counter_bytes,
            hashlib.sha256,
        ).digest()
        output.extend(block)
        counter += 1

    return bytes(output[:length])


def _xor_bytes(left, right):
    return bytes(a ^ b for a, b in zip(left, right))


def encrypt_message(message, shared_secret=None):
    """
    Protect a UDP payload with confidentiality and integrity checks
    """
    if not isinstance(message, str):
        raise TypeError("message must be a string")

    resolved_secret = _resolve_shared_secret(shared_secret)
    encryption_key, mac_key = _derive_keys(resolved_secret)
    nonce = secrets.token_bytes(NONCE_SIZE)
    plaintext = message.encode("utf-8")
    keystream = _build_keystream(encryption_key, nonce, len(plaintext))
    ciphertext = _xor_bytes(plaintext, keystream)
    tag = hmac.new(mac_key, nonce + ciphertext, hashlib.sha256).digest()

    nonce_b64 = base64.urlsafe_b64encode(nonce).decode("ascii")
    ciphertext_b64 = base64.urlsafe_b64encode(ciphertext).decode("ascii")
    tag_b64 = base64.urlsafe_b64encode(tag).decode("ascii")

    return f"{SECURE_PACKET_VERSION}.{nonce_b64}.{ciphertext_b64}.{tag_b64}"


def decrypt_message(packet, shared_secret=None):
    """
    Verify and decrypt a protected UDP payload
    """
    try:
        version, nonce_b64, ciphertext_b64, tag_b64 = packet.split(".", 3)
    except ValueError as exc:
        raise ValueError("Invalid secure packet format") from exc

    if version != SECURE_PACKET_VERSION:
        raise ValueError("Unsupported secure packet version")

    resolved_secret = _resolve_shared_secret(shared_secret)
    encryption_key, mac_key = _derive_keys(resolved_secret)
    nonce = base64.urlsafe_b64decode(nonce_b64.encode("ascii"))
    ciphertext = base64.urlsafe_b64decode(ciphertext_b64.encode("ascii"))
    received_tag = base64.urlsafe_b64decode(tag_b64.encode("ascii"))

    expected_tag = hmac.new(mac_key, nonce + ciphertext, hashlib.sha256).digest()
    if not hmac.compare_digest(received_tag, expected_tag):
        raise ValueError("Secure packet authentication failed")

    keystream = _build_keystream(encryption_key, nonce, len(ciphertext))
    plaintext = _xor_bytes(ciphertext, keystream)
    return plaintext.decode("utf-8")
