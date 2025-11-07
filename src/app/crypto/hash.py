"""
Cryptographic hash operations.

:author: Max Milazzo
"""



import hashlib



def generate(input: str) -> str:
    """
    Hashes a given string using SHA-256 and returns the hex digest.

    :param input: input string
    :return: hash value of input string
    """

    sha256_hash = hashlib.sha256(input.encode())

    return sha256_hash.hexdigest()