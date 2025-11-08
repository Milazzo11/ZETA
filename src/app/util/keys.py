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
    PRIV_KEY = f.read()

PRIV_KEY = PRIV_KEY.decode("utf-8")
# load server private key from file


with open(PUB_KEY_FILE, "rb") as f:
    PUB_KEY = f.read()

PUB_KEY = PUB_KEY.decode("utf-8")
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


def priv() -> str:
    """
    Loads the server private key.

    :return: private key string
    """

    return PRIV_KEY


def pub() -> str:
    """
    Loads the server public key.

    :return: private key string
    """
    
    return PUB_KEY