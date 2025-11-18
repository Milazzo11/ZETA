"""
Cryptographic hash operations.

:author: Max Milazzo
"""



import base64
import hashlib



def generate_bytes(input: str) -> bytes:
    """
    Hashes a given byte sequence using SHA-256 and returns the raw digest bytes.

    :param input_bytes: input bytes
    :return: SHA-256 digest (raw bytes)
    """

    hash = hashlib.sha256(input.encode())

    return hash.digest()


def generate_string(input: str) -> str:
    """
    Hashes a given string using SHA-256 and returns a string representation (base64).

    :param input: input string
    :return: base64-encoded hash value of input string
    """

    digest = generate_bytes(input)

    return base64.b64encode(digest).decode()