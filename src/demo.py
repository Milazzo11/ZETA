
import app.util.flags as flags

flags.demo = True

from app.API.models import *
from app.data.event import Event
import time
import requests

from app.crypto.asymmetric import AKC
from app.util import keys


import uuid
import time


###NOTE -- FIGURE OUT HOW TO DO IMPORTS WITHOUT GLOBAL CODE RUNNING


SERVER_URL = "http://localhost:8000"


TIMESTAMP_ERROR = 10




def auth_req(content, private_key, public_key, request_type):
    """
    """

    packet = Data[request_type].load(content)
    cipher = AKC(private_key=private_key)

    return Auth[request_type](
        data=packet, public_key=public_key,
        signature=cipher.sign(packet.model_dump())
    )

    ### TODO - eventally modify Auth load to make this more accessible


def auth_res(res_json) -> bool:
    """
    """

    now = time.time()

    if abs(now - res_json["data"]["timestamp"]) > TIMESTAMP_ERROR:
        return False

    cipher = AKC(public_key=keys.pub())
    return cipher.verify(res_json["signature"], res_json["data"])


def parse_res(res):
    """
    """

    res_json = res.json()

    print(res.status_code, res_json)
    print("RESPONSE AUTH:", auth_res(res_json))
    print()

    return res_json




def scenario_1():
    """
    """

    print("\nBeverly creates a new event: \"Tea Party\"")
    input("> ")

    cipher = AKC()
    beverly_private_key = cipher.private_key
    beverly_public_key = cipher.public_key

    req = auth_req(
        CreateRequest(
            event=Event(
                name="Tea Party",
                description="Tea, earl grey, hot",
                tickets=16,
                start=time.time(),
                finish=time.time() + 2_628_00,
                restricted=False
            )
        ),
        beverly_private_key,
        beverly_public_key,
        CreateRequest
    ).model_dump()
    res = requests.post(SERVER_URL + "/create", json=req)
    res_json = parse_res(res)

    event_id = res_json["data"]["content"]["event_id"]

    #####

    print("\nJean-Luc wants to join her, so he searches \"tea\" to find the event ID, then registers")
    input("> ")

    cipher = AKC()
    jean_luc_private_key = cipher.private_key
    jean_luc_public_key = cipher.public_key

    req = auth_req(
        SearchRequest(text="tea", mode="text"),
        jean_luc_private_key,
        jean_luc_public_key,
        SearchRequest
    ).model_dump()
    res = requests.post(SERVER_URL + "/search", json=req)
    parse_res(res)

    #####

    req = auth_req(
        RegisterRequest(event_id=event_id),
        jean_luc_private_key,
        jean_luc_public_key,
        RegisterRequest
    ).model_dump()
    res = requests.post(SERVER_URL + "/register", json=req)
    res_json = parse_res(res)

    jean_luc_ticket = res_json["data"]["content"]["ticket"]

    print("\nUnfortunately, Jean-Luc is busy the day of the party, so he decides to give his ticket to his friend Geordi")
    input("> ")

    #####

    cipher = AKC()
    geordi_private_key = cipher.private_key
    geordi_public_key = cipher.public_key

    
    print("\nFirst, he signs a \"transfer request\" and gives it to Geordi:\n")

    transfer = auth_req(
        Transfer(
            ticket=jean_luc_ticket,
            transfer_public_key=geordi_public_key
        ),
        jean_luc_private_key,
        jean_luc_public_key,
        Transfer
    )

    print(transfer.model_dump())

    print("\nGeordi can now include this signed chunk of data in his request to the server for a transfer to prove cooperation\n")

    req = auth_req(
        TransferRequest(
            event_id=event_id,
            transfer=transfer
        ),
        geordi_private_key,
        geordi_public_key,
        TransferRequest
    ).model_dump()
    res = requests.post(SERVER_URL + "/transfer", json=req)
    res_json = parse_res(res)

    geordi_ticket = res_json["data"]["content"]["ticket"]

    #####

    print("\nJean-Luc is curious what will happen if he tries to redeem his transferred ticket, though")
    input("> ")

    req = auth_req(
        RedeemRequest(
            event_id=event_id,
            ticket=jean_luc_ticket
        ),
        jean_luc_private_key,
        jean_luc_public_key,
        RedeemRequest
    ).model_dump()
    res = requests.post(SERVER_URL + "/redeem", json=req)
    parse_res(res)

    print("\nWhat about if he tries to transfer Geordi his ticket for a second time?\n")

    transfer = auth_req(
        Transfer(
            ticket=jean_luc_ticket,
            transfer_public_key=geordi_public_key
        ),
        jean_luc_private_key,
        jean_luc_public_key,
        Transfer
    )

    req = auth_req(
        TransferRequest(
            event_id=event_id,
            transfer=transfer
        ),
        geordi_private_key,
        geordi_public_key,
        TransferRequest
    ).model_dump()
    res = requests.post(SERVER_URL + "/transfer", json=req)
    parse_res(res)

    #####

    print("\nNow, Geordi shows up to the event and is verified by Beverly")
    input("> ")

    print("\nFirst, she checks that he has not yet redeemed his ticket\n")

    req = auth_req(
        VerifyRequest(
            event_id=event_id,
            ticket=geordi_ticket,
            check_public_key=geordi_public_key
        ),
        beverly_private_key,
        beverly_public_key,
        VerifyRequest
    ).model_dump()
    res = requests.post(SERVER_URL + "/verify", json=req)
    parse_res(res)

    print("\nNow Beverly attempts to redeem his ticket for him\n")

    req = auth_req(
        RedeemRequest(
            event_id=event_id,
            ticket=geordi_ticket
        ),
        beverly_private_key,
        beverly_public_key,
        RedeemRequest
    ).model_dump()
    res = requests.post(SERVER_URL + "/redeem", json=req)
    parse_res(res)

    req = auth_req(
        VerifyRequest(
            event_id=event_id,
            ticket=geordi_ticket,
            check_public_key=geordi_public_key
        ),
        beverly_private_key,
        beverly_public_key,
        VerifyRequest
    ).model_dump()
    res = requests.post(SERVER_URL + "/verify", json=req)
    parse_res(res)

    #####

    print("\nThis is unsuccessful, however, and Geordi now needs to provide his signature to proceed with redemption")
    input("> ")

    req = auth_req(
        RedeemRequest(
            event_id=event_id,
            ticket=geordi_ticket
        ),
        geordi_private_key,
        geordi_public_key,
        RedeemRequest
    ).model_dump()
    res = requests.post(SERVER_URL + "/redeem", json=req)
    parse_res(res)


    print("\nTo see what happens, Geordi attempts to redeem the ticket a 2nd time (which fails obviously)\n")

    req = auth_req(
        RedeemRequest(
            event_id=event_id,
            ticket=geordi_ticket
        ),
        geordi_private_key,
        geordi_public_key,
        RedeemRequest
    ).model_dump()
    res = requests.post(SERVER_URL + "/redeem", json=req)
    parse_res(res)

    print("\nAnd now, finally, Beverly can confirm Geordi's redemption\n")

    req = auth_req(
        VerifyRequest(
            event_id=event_id,
            ticket=geordi_ticket,
            check_public_key=geordi_public_key
        ),
        beverly_private_key,
        beverly_public_key,
        VerifyRequest
    ).model_dump()
    res = requests.post(SERVER_URL + "/verify", json=req)
    parse_res(res)

    #####

    print("\nLater on, Jean-Luc asks Beverly to attempt a verification with his outdated ticket\n")

    req = auth_req(
        VerifyRequest(
            event_id=event_id,
            ticket=jean_luc_ticket,
            check_public_key=jean_luc_public_key
        ),
        beverly_private_key,
        beverly_public_key,
        VerifyRequest
    ).model_dump()
    res = requests.post(SERVER_URL + "/verify", json=req)
    parse_res(res)

    print("\n... which, of course, fails.\n")
    print("And finally, Geordi and Jean-Luc see what happens if he tries to transfer him an already redeemed ticket")
    
    transfer = auth_req(
        Transfer(
            ticket=geordi_ticket,
            transfer_public_key=jean_luc_public_key
        ),
        geordi_private_key,
        geordi_public_key,
        Transfer
    )

    req = auth_req(
        TransferRequest(
            event_id=event_id,
            transfer=transfer
        ),
        jean_luc_private_key,
        jean_luc_public_key,
        TransferRequest
    ).model_dump()
    res = requests.post(SERVER_URL + "/transfer", json=req)
    parse_res(res)

    #####

    print("\nevent deletion test cases\n")

    # normal id search
    req = auth_req(
        SearchRequest(text=event_id, mode="id"),
        beverly_private_key,
        beverly_public_key,
        SearchRequest
    ).model_dump()
    res = requests.post(SERVER_URL + "/search", json=req)
    parse_res(res)

    # fail
    req = auth_req(
        DeleteRequest(event_id=event_id),
        jean_luc_private_key,
        jean_luc_public_key,
        DeleteRequest
    ).model_dump()
    res = requests.post(SERVER_URL + "/delete", json=req)
    parse_res(res)

    # success
    req = auth_req(
        DeleteRequest(event_id=event_id),
        beverly_private_key,
        beverly_public_key,
        DeleteRequest
    ).model_dump()
    res = requests.post(SERVER_URL + "/delete", json=req)
    parse_res(res)

    # empty search
    req = auth_req(
        SearchRequest(text=event_id, mode="id"),
        beverly_private_key,
        beverly_public_key,
        SearchRequest
    ).model_dump()
    res = requests.post(SERVER_URL + "/search", json=req)
    parse_res(res)

    # fail
    req = auth_req(
        DeleteRequest(event_id=event_id),
        beverly_private_key,
        beverly_public_key,
        DeleteRequest
    ).model_dump()
    res = requests.post(SERVER_URL + "/delete", json=req)
    parse_res(res)



def scenario_2():
    """
    """

    print("\nDeanna creates a new event: \"Counseling Session\"\n")

    cipher = AKC()
    deanna_private_key = cipher.private_key
    deanna_public_key = cipher.public_key

    req = auth_req(
        CreateRequest(
            event=Event(
                name="Counseling Session",
                description="Betazoid empathy",
                tickets=2,
                start=time.time(),
                finish=time.time() + 2_628_00,
                restricted=True
            )
        ),
        deanna_private_key,
        deanna_public_key,
        CreateRequest
    ).model_dump()
    res = requests.post(SERVER_URL + "/create", json=req)
    res_json = parse_res(res)

    event_id = res_json["data"]["content"]["event_id"]

    print("\nNow she quickly resubmits the message to see what happens\n")

    res = requests.post(SERVER_URL + "/create", json=req)
    parse_res(res)

    print("\nShe also tests submitting a request with an expired timestamp\n")

    req["data"]["timestamp"] -= TIMESTAMP_ERROR
    res = requests.post(SERVER_URL + "/create", json=req)
    parse_res(res)

    print("\n... and a request with data modified post-signature\n")

    req["data"]["nonce"] = str(uuid.uuid4())
    req["data"]["timestamp"] = time.time()
    res = requests.post(SERVER_URL + "/create", json=req)
    parse_res(res)

    #####

    print("\nWilliam gets the event ID from Deanna and he attempts to register")
    input("> ")

    cipher = AKC()
    william_private_key = cipher.private_key
    william_public_key = cipher.public_key

    req = auth_req(
        RegisterRequest(event_id=event_id),
        william_private_key,
        william_public_key,
        RegisterRequest
    ).model_dump()
    res = requests.post(SERVER_URL + "/register", json=req)
    parse_res(res)

    print("\n... but it fails???")
    input(">")

    ## William successfully registers with verification + custom metadata

    print("\nAnd after talking to Deanna, he realizes that he needs a verification from her to receive a ticket")
    print("\nSo she signs a verification request containing his public key and gives it to him\n")

    verification = auth_req(
        Verification(
            event_id=event_id,
            public_key=william_public_key,
            metadata="Imzadi <3"
        ),
        deanna_private_key,
        deanna_public_key,
        Verification
    )

    print(verification.model_dump())

    print("\nAnd now William includes this verification in his request and successfully registers")

    req = auth_req(
        RegisterRequest(
            event_id=event_id,
            verification=verification
        ),
        william_private_key,
        william_public_key,
        RegisterRequest
    ).model_dump()
    res = requests.post(SERVER_URL + "/register", json=req)
    res_json = parse_res(res)

    william_ticket = res_json["data"]["content"]["ticket"]

    #####

    print("\nReginald also wants to join the event, so Deanna gives him a signed verification block to use")
    print("... but unknowingly, she accidentally signs it on William's public key!\n")
    input(">")

    verification = auth_req(
        Verification(
            event_id=event_id,
            public_key=william_public_key,
            metadata="Broccoli"
        ),
        deanna_private_key,
        deanna_public_key,
        Verification
    )

    print("\nReginald attempts to register... but obviously it doesn't work\n")

    cipher = AKC()
    reginald_private_key = cipher.private_key
    reginald_public_key = cipher.public_key

    req = auth_req(
        RegisterRequest(
            event_id=event_id,
            verification=verification
        ),
        reginald_private_key,
        reginald_public_key,
        RegisterRequest
    ).model_dump()
    res = requests.post(SERVER_URL + "/register", json=req)
    parse_res(res)

    #####

    print("Deanna fixes the verification block and Reginald tries again with success")
    input("> ")

    verification = auth_req(
        Verification(
            event_id=event_id,
            public_key=reginald_public_key,
            # metadata="Broccoli"
        ),
        deanna_private_key,
        deanna_public_key,
        Verification
    )

    req = auth_req(
        RegisterRequest(
            event_id=event_id,
            verification=verification
        ),
        reginald_private_key,
        reginald_public_key,
        RegisterRequest
    ).model_dump()
    res = requests.post(SERVER_URL + "/register", json=req)
    res_json = parse_res(res)

    reginald_ticket = res_json["data"]["content"]["ticket"]

    ## Wesley can't register bc event is full

    print("Now it is Wesley's turn to register... Deanna provides him verification and he makes the request")
    input("> ")

    cipher = AKC()
    wesley_private_key = cipher.private_key
    wesley_public_key = cipher.public_key


    verification = auth_req(
        Verification(
            event_id=event_id,
            public_key=wesley_public_key,
            metadata="annoying ass mf"
        ),
        deanna_private_key,
        deanna_public_key,
        Verification
    )

    req = auth_req(
        RegisterRequest(
            event_id=event_id,
            verification=verification
        ),
        wesley_private_key,
        wesley_public_key,
        RegisterRequest
    ).model_dump()
    res = requests.post(SERVER_URL + "/register", json=req)
    parse_res(res)

    print("\nBut oh no!  The event is full :/")
    print("Did Deanna do it on purpose because Wesley is super annoying?  It's anyone's guess!")
    input("> ")

    ## William/Reginals redeem and then do verif (we see custom metadata)








    print("\nNow Reginald is verified at the session (verify->redeem->verify)\n")

    req = auth_req(
        VerifyRequest(
            event_id=event_id,
            ticket=reginald_ticket,
            check_public_key=reginald_public_key
        ),
        deanna_private_key,
        deanna_public_key,
        VerifyRequest
    ).model_dump()
    res = requests.post(SERVER_URL + "/verify", json=req)
    parse_res(res)

    req = auth_req(
        RedeemRequest(
            event_id=event_id,
            ticket=reginald_ticket
        ),
        reginald_private_key,
        reginald_public_key,
        RedeemRequest
    ).model_dump()
    res = requests.post(SERVER_URL + "/redeem", json=req)
    parse_res(res)

    req = auth_req(
        VerifyRequest(
            event_id=event_id,
            ticket=reginald_ticket,
            check_public_key=reginald_public_key
        ),
        deanna_private_key,
        deanna_public_key,
        VerifyRequest
    ).model_dump()
    res = requests.post(SERVER_URL + "/verify", json=req)
    parse_res(res)

    
    print("... and so is William")

    req = auth_req(
        VerifyRequest(
            event_id=event_id,
            ticket=william_ticket,
            check_public_key=william_public_key
        ),
        deanna_private_key,
        deanna_public_key,
        VerifyRequest
    ).model_dump()
    res = requests.post(SERVER_URL + "/verify", json=req)
    parse_res(res)

    req = auth_req(
        RedeemRequest(
            event_id=event_id,
            ticket=william_ticket
        ),
        william_private_key,
        william_public_key,
        RedeemRequest
    ).model_dump()
    res = requests.post(SERVER_URL + "/redeem", json=req)
    parse_res(res)

    req = auth_req(
        VerifyRequest(
            event_id=event_id,
            ticket=william_ticket,
            check_public_key=william_public_key
        ),
        deanna_private_key,
        deanna_public_key,
        VerifyRequest
    ).model_dump()
    res = requests.post(SERVER_URL + "/verify", json=req)
    parse_res(res)


    #### event deletion

    # normal search
    req = auth_req(
        SearchRequest(text=event_id, mode="id"),
        deanna_private_key,
        deanna_public_key,
        SearchRequest
    ).model_dump()
    res = requests.post(SERVER_URL + "/search", json=req)
    parse_res(res)


    # success
    req = auth_req(
        DeleteRequest(event_id=event_id),
        deanna_private_key,
        deanna_public_key,
        DeleteRequest
    ).model_dump()
    res = requests.post(SERVER_URL + "/delete", json=req)
    parse_res(res)

    
    # empty search
    req = auth_req(
        SearchRequest(text=event_id, mode="id"),
        deanna_private_key,
        deanna_public_key,
        SearchRequest
    ).model_dump()
    res = requests.post(SERVER_URL + "/search", json=req)
    parse_res(res)





def main():
    """
    """

    print("ZETA demo!")
    print("PRESS ENTER TO START")
    input("> ")

    #scenario_1()
    input("> ")

    scenario_2()
    input("> ")

    ## CREATE ENDPOINT and then demonstrate the deletion of both events






if __name__ == "__main__":
    main()