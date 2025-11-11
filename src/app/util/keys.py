"""
Key management module.

:author: Max Milazzo
"""



from app.crypto.asymmetric import AKC

import os



PRIV_KEY_FILE = os.path.join("data", "priv.key")
# private key file


PUB_KEY_FILE = os.path.join("data", "pub.key")
# public key file


with open(PRIV_KEY_FILE, "rb") as f:
    PRIVATE_KEY = f.read()

PRIVATE_KEY = PRIVATE_KEY.decode("utf-8")
# load server private key from file


with open(PUB_KEY_FILE, "rb") as f:
    PUBLIC_KEY = f.read()

PUBLIC_KEY = PUBLIC_KEY.decode("utf-8")
# load server public key from file



def setup() -> None:
    """
    Set up server keys.
    """

    cipher = AKC()

    with open(PRIV_KEY_FILE, "wb") as f:
        f.write(cipher.private_key)
        
    with open(PUB_KEY_FILE, "wb") as f:
        f.write(cipher.public_key)