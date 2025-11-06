"""
Cryptographic hash operations.

:author: Max Milazzo
"""



import hashlib


def generate(input_string: str) -> str:
    """
    Hashes a given string using SHA-256 and returns the hex digest.
    """

    sha256_hash = hashlib.sha256(input_string.encode())
    return sha256_hash.hexdigest()