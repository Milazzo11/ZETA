from setup import PRIV_KEY_FILE, PUB_KEY_FILE



with open(PRIV_KEY_FILE, "rb") as f:
    PRIV_KEY = f.read()

PRIV_KEY = PRIV_KEY.decode("utf-8")


with open(PUB_KEY_FILE, "rb") as f:
    PUB_KEY = f.read()

PUB_KEY = PUB_KEY.decode("utf-8")



def priv() -> str:
    """
    """

    return PRIV_KEY


def pub() -> str:
    """
    """
    
    return PUB_KEY