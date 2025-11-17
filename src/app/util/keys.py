"""
Key management module.

:author: Max Milazzo
"""



from app.crypto.asymmetric import AKC

import os



PRIV_KEY_FILE = os.path.join("data", "priv.key")
PUB_KEY_FILE = os.path.join("data", "pub.key")
# key file locations



def setup() -> str:
    """
    Generate a new server keypair, write it to disk, and return the private key.
    """

    cipher = AKC()
    # generate new keypair

    with open(PRIV_KEY_FILE, "w", encoding="utf-8") as f:
        f.write(cipher.private_key)

    with open(PUB_KEY_FILE, "w", encoding="utf-8") as f:
        f.write(cipher.public_key)

    return cipher.private_key


if os.path.exists(PRIV_KEY_FILE):
    with open(PRIV_KEY_FILE, "r", encoding="utf-8") as f:
        PRIVATE_KEY = f.read()

else:
    PRIVATE_KEY = setup()


RESPONSE_SIGNER = AKC(private_key=PRIVATE_KEY)
# single signer instance for server responses