from app.API.models import *
from app.data.event import Event
import time
import requests

from app.crypto.asymmetric import AKE
from app.util import keys


###TODO -- this needs to actually be built well


SERVER_URL = "http://localhost:8000"


TIMESTAMP_ERROR = 10



def auth_req(content, private_key, public_key, request_type):
    """
    """

    packet = Data[request_type].load(content)
    cipher = AKE(private_key=private_key)

    return Auth[request_type](
        data=packet, public_key=public_key,
        signature=cipher.sign(packet.to_dict())
    ).to_dict()


def auth_res(res_json) -> bool:
    """
    """

    now = time.time()

    if abs(now - res_json["data"]["timestamp"]) > TIMESTAMP_ERROR:
        return False

    cipher = AKE(public_key=keys.pub())
    return cipher.verify(res_json["signature"], res_json["data"])



def main():
    """
    """

    print("ZETA demo!")
    print("PRESS ENTER TO START")
    input("> ")

    print("\nKathryn creates a new event: \"Coming Home Party\"")

    cipher = AKE()
    kathryn_private_key = cipher.private_key
    kathryn_public_key = cipher.public_key

    req = auth_req(
        CreateRequest(
            event=Event(
                name="Coming Home Party",
                description="No place like home",
                tickets=128,
                start=time.time(),
                end=time.time() + 2_628_00,
                private=False,
            )
        ),
        kathryn_private_key,
        kathryn_public_key,
        CreateRequest
    )
    res = requests.post(SERVER_URL + "/create", json=req)

    res_json = res.json()
    print(res.status_code, res_json)
    print("RESPONSE AUTH:", auth_res(res_json))

if __name__ == "__main__":
    main()