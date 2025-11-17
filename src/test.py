"""
Testing/demonstration module.

:author: Max Milazzo
"""



from app.API.models.base import Auth, ErrorResponse
from app.API.models.base.auth import TIMESTAMP_ERROR
from app.API.models.endpoints import *
from app.API.models.endpoints.register import Verification
from app.API.models.endpoints.transfer import Transfer
from app.crypto.asymmetric import AKC
from app.data.models.event import Event
from app.util import display

import requests
import time
import uuid
from typing import Any



SERVER_URL = "http://localhost:8000"
# server URL



def output(
    request: Auth[Any],
    response: Auth[Any],
    status_code: int,
    expected_code: int,
    auth: bool = True
) -> None:
    """
    Compact request/response logging with STATUS first and an auth verdict.

    :param request: the original request
    :param response: the server response
    :param status_code: HTTP response status code
    :param expected_code: expected HTTP response status code
    :param auth: perform request authentication if True
    """

    if auth:
        response.authenticate()

    print("====================")
    print("STATUS:", status_code)
    print("\nREQUEST:", request.model_dump())
    print("\nRESPONSE:", response.model_dump())
    print()

    input("> ")
    display.clear()

    assert status_code == expected_code, f"{status_code} != {expected_code}"


##########

print("ZETA Demo")
input("> Press Enter to begin... ")

Auth.start_service(redis_url=None)
# start the authentication nonce-tracker service (in-memory version)

display.clear()

jean_luc = AKC()
beverly  = AKC()
wesley = AKC()
geordi = AKC()
william = AKC()
deanna = AKC()

##########

print(
    "After what seems like a lifetime of practice, Jean-Luc is excited to " \
    'show off his flute skills, so he creates a new event: "Flute Recital."'
)

req = Auth[CreateRequest].load(
    CreateRequest(
        event=Event(
            name="Flute Recital",
            description="Ressikan flute performance",
            tickets=3,
            restricted=False,
            transfer_limit=63
        )
    ),
    jean_luc
)
res = requests.post(SERVER_URL + "/create", json=req.model_dump())
output(req, Auth[CreateResponse](**res.json()), res.status_code, 200)

event_id_1 = res.json()["data"]["content"]["event_id"]
assert len(event_id_1) == 36, f"{len(event_id_1)} != 36"

##########

print("Beverly wants to see him play, so she searches for the event.")

req = Auth[SearchRequest].load(
    SearchRequest(
        text="flute",
        mode="text"
    ),
    beverly
)
res = requests.post(SERVER_URL + "/search", json=req.model_dump())
output(req, Auth[SearchResponse](**res.json()), res.status_code, 200)

assert len(res.json()["data"]["content"]["events"]) > 0, (
    f"{len(res.json()["data"]["content"]["events"])} !> 0"
)

##########

print("And now that she has the event ID, she registers for the recital.")

req = Auth[RegisterRequest].load(
    RegisterRequest(
        event_id=event_id_1
    ),
    beverly
)
res = requests.post(SERVER_URL + "/register", json=req.model_dump())
output(req, Auth[RegisterResponse](**res.json()), res.status_code, 200)

beverly_ticket = res.json()["data"]["content"]["ticket"]
assert beverly_ticket is not None, "None is None"

##########

print(
    "Berverly's son Wesley wants to attend too, but he is currently grounded "
    "for covering up his former classmate's death.  He's not going to let " \
    "that stop him, though, and so he tries to submit a forged request to " \
    "transfer his mom's ticket to him."
)

wesley_forged = AKC(private_key=wesley.private_key)
wesley_forged.public_key = beverly.public_key

req = Auth[TransferRequest].load(
    TransferRequest(
        event_id=event_id_1,
        transfer=Auth[Transfer].load(
            Transfer(
                ticket=beverly_ticket,
                transfer_public_key=wesley.public_key
            ),
            wesley_forged
        )
    ),
    wesley
)
res = requests.post(SERVER_URL + "/transfer", json=req.model_dump())
output(req, Auth[ErrorResponse](**res.json()), res.status_code, 403)

assert res.json()["data"]["content"]["detail"] == "signature verification failed", (
    f"{repr(res.json()["data"]["content"]["detail"])} != 'signature verification failed'"
)

##########

print(
    "Upset that it didn't work, Wesley decides to attempt to cancel his " \
    "mom's ticket out of spite -- spoofing Jean-Luc's (the event owner) " \
    "signature this time."
)

wesley_forged = AKC(private_key=wesley.private_key)
wesley_forged.public_key = jean_luc.public_key

req = Auth[CancelRequest].load(
    CancelRequest(
        event_id=event_id_1,
        ticket=beverly_ticket,
        check_public_key=beverly.public_key
    ),
    wesley_forged
)
res = requests.post(SERVER_URL + "/cancel", json=req.model_dump())
output(req, Auth[ErrorResponse](**res.json()), res.status_code, 403)

assert res.json()["data"]["content"]["detail"] == "signature verification failed", (
    f"{repr(res.json()["data"]["content"]["detail"])} != 'signature verification failed'"
)

##########

print(
    "After finding out about her son's actions, she decides that she " \
    "unfortunately will not be attending the flute recital so that she can " \
    "instead give Wesley a much needed beating.  Her friend Goerdi, " \
    "however, does want to attend, and so Beverly transfers her ticket to " \
    "him... legitimately this time!  She sends him a properly authorized " \
    "transfer validation block, and Geordi makes the request."
)

req = Auth[TransferRequest].load(
    TransferRequest(
        event_id=event_id_1,
        transfer=Auth[Transfer].load(
            Transfer(
                ticket=beverly_ticket,
                transfer_public_key=geordi.public_key
            ),
            beverly
        )
    ),
    geordi
)
res = requests.post(SERVER_URL + "/transfer", json=req.model_dump())
output(req, Auth[TransferResponse](**res.json()), res.status_code, 200)

geordi_ticket = res.json()["data"]["content"]["ticket"]
assert geordi_ticket is not None, "None is None"

##########

print(
    "Wesley isn't willing to give up so easily, though... so he steals " \
    "his mother's old ticket and digital signature credentials while she " \
    "is distracted and manages to slip out before his scheduled beating can " \
    "begin.  Oblivious to the fact that the ticket he has was transrrered " \
    "away, he shows up to the recital and attempts to redeem it."
)

req = Auth[RedeemRequest].load(
    RedeemRequest(
        event_id=event_id_1,
        ticket=beverly_ticket
    ),
    beverly
)
res = requests.post(SERVER_URL + "/redeem", json=req.model_dump())
output(req, Auth[ErrorResponse](**res.json()), res.status_code, 409)

assert res.json()["data"]["content"]["detail"] == "ticket superseded", (
    f"{repr(res.json()["data"]["content"]["detail"])} != 'ticket superseded'"
)

##########

print(
    "Still not ready to concede, Wesley comes up with a new ingenious plan: " \
    "He will simply transfer his mom's non-functional ticket to himself, " \
    "and then surely everything will work for him."
)

req = Auth[TransferRequest].load(
    TransferRequest(
        event_id=event_id_1,
        transfer=Auth[Transfer].load(
            Transfer(
                ticket=beverly_ticket,
                transfer_public_key=wesley.public_key
            ),
            beverly
        )
    ),
    wesley
)
res = requests.post(SERVER_URL + "/transfer", json=req.model_dump())
output(req, Auth[ErrorResponse](**res.json()), res.status_code, 409)

assert res.json()["data"]["content"]["detail"] == "ticket superseded", (
    f"{repr(res.json()["data"]["content"]["detail"])} != 'ticket superseded'"
)

##########

print(
    "A bit frustrated now, he sees Geordi about to enter the recital.  " \
    "He quickly steals a copy of Geordi's ticket and public key to check if " \
    "it has already been redeemed.  This endpoint is available to all users " \
    "to promote transfer transparency... but Wesley plans to use it for evil!"
)

req = Auth[VerifyRequest].load(
    VerifyRequest(
        event_id=event_id_1,
        ticket=geordi_ticket,
        check_public_key=geordi.public_key
    ),
    wesley
)
res = requests.post(SERVER_URL + "/verify", json=req.model_dump())
output(req, Auth[VerifyResponse](**res.json()), res.status_code, 200)

assert res.json()["data"]["content"]["redeemed"] == False, (
    f"{repr(res.json()["data"]["content"]["redeemed"])} != False"
)
assert res.json()["data"]["content"]["stamped"] is None, (
    f"{repr(res.json()["data"]["content"]["stamped"])} is not None"
)
assert res.json()["data"]["content"]["version"] == 2, (
    f"{repr(res.json()["data"]["content"]["version"]) != 2}"
)
assert res.json()["data"]["content"]["transfer_limit"] == 63, (
    f"{repr(res.json()["data"]["content"]["transfer_limit"]) != 63}"
)
assert res.json()["data"]["content"]["metadata"] is None, (
    f"{repr(res.json()["data"]["content"]["metadata"])} is not None"
)

##########

print(
    "Upon seeing Geordi, Jean-Luc gets so excited that he takes Geordi's " \
    "ticket and tries to make a redemption request for him."
)

req = Auth[RedeemRequest].load(
    RedeemRequest(
        event_id=event_id_1,
        ticket=geordi_ticket
    ),
    jean_luc
)
res = requests.post(SERVER_URL + "/redeem", json=req.model_dump())
output(req, Auth[ErrorResponse](**res.json()), res.status_code, 400)

assert res.json()["data"]["content"]["detail"] == "ticket for different user", (
    f"{repr(res.json()["data"]["content"]["detail"])} != 'ticket for different user'"
)

##########

print(
    '"No matter," he thinks; he will simply skip redemption and proceed to ' \
    "ticket verification and stamping.  So Jean-Luc makes a verification/" \
    "stamping request in an attempt to confirm and mark Geordi as admitted."
)

req = Auth[VerifyRequest].load(
    VerifyRequest(
        event_id=event_id_1,
        ticket=geordi_ticket,
        check_public_key=geordi.public_key,
        stamp=True
    ),
    jean_luc
)
res = requests.post(SERVER_URL + "/verify", json=req.model_dump())
output(req, Auth[ErrorResponse](**res.json()), res.status_code, 409)

assert res.json()["data"]["content"]["detail"] == "ticket has not been redeemed", (
    f"{repr(res.json()["data"]["content"]["detail"])} != 'ticket has not been redeemed'"
)

##########

print(
    "Geordi finally makes the redemption request himself... however, Wesley " \
    "attempts to jam the signal, and the request reaches the server with a " \
    "few of the encrypted ticket ciphertext bytes mixed up."
)

bad_ticket = geordi_ticket[:-1] + ("A" if geordi_ticket[-1] != "A" else "B")

req = Auth[RedeemRequest].load(
    RedeemRequest(
        event_id=event_id_1,
        ticket=bad_ticket
    ),
    geordi
)
res = requests.post(SERVER_URL + "/redeem", json=req.model_dump())
output(req, Auth[ErrorResponse](**res.json()), res.status_code, 403)

assert res.json()["data"]["content"]["detail"] == "ticket verification failed", (
    f"{repr(res.json()["data"]["content"]["detail"])} != 'ticket verification failed'"
)

##########

print(
    "Unsure what had just happened, Geordi retries the redemption.  And " \
    "thankfully for him, Wesley's signal jammer just ran out of power, " \
    "so his request reaches the server unaltered."
)

req = Auth[RedeemRequest].load(
    RedeemRequest(
        event_id=event_id_1,
        ticket=geordi_ticket
    ),
    geordi
)
res = requests.post(SERVER_URL + "/redeem", json=req.model_dump())
output(req, Auth[RedeemResponse](**res.json()), res.status_code, 200)

assert res.json()["data"]["content"]["success"] == True, (
    f"{repr(res.json()["data"]["content"]["success"])} != True"
)

##########

print("Without thinking, Geordi then attempts to stamp his own ticket.")

req = Auth[VerifyRequest].load(
    VerifyRequest(
        event_id=event_id_1,
        ticket=geordi_ticket,
        check_public_key=geordi.public_key,
        stamp=True
    ),
    geordi
)
res = requests.post(SERVER_URL + "/verify", json=req.model_dump())
output(req, Auth[ErrorResponse](**res.json()), res.status_code, 403)

assert res.json()["data"]["content"]["detail"] == "only event owners may stamp tickets", (
    f"{repr(res.json()["data"]["content"]["detail"])} != 'only event owners may stamp tickets'"
)

##########

print("Finally, Jean-Luc sends a proper verify/stamp request to admit Geordi")

req = Auth[VerifyRequest].load(
    VerifyRequest(
        event_id=event_id_1,
        ticket=geordi_ticket,
        check_public_key=geordi.public_key,
        stamp=True
    ),
    jean_luc
)
res = requests.post(SERVER_URL + "/verify", json=req.model_dump())
output(req, Auth[VerifyResponse](**res.json()), res.status_code, 200)

assert res.json()["data"]["content"]["redeemed"] == True, (
    f"{repr(res.json()["data"]["content"]["redeemed"])} != True"
)
assert res.json()["data"]["content"]["stamped"] == True, (
    f"{repr(res.json()["data"]["content"]["stamped"])} != True"
)
assert res.json()["data"]["content"]["version"] == 2, (
    f"{repr(res.json()["data"]["content"]["version"]) != 2}"
)
assert res.json()["data"]["content"]["transfer_limit"] == 63, (
    f"{repr(res.json()["data"]["content"]["transfer_limit"]) != 63}"
)
assert res.json()["data"]["content"]["metadata"] is None, (
    f"{repr(res.json()["data"]["content"]["metadata"])} is not None"
)

##########

print("...And just to make sure, he stamps it for a second time too!")

req = Auth[VerifyRequest].load(
    VerifyRequest(
        event_id=event_id_1,
        ticket=geordi_ticket,
        check_public_key=geordi.public_key,
        stamp=True
    ),
    jean_luc
)
res = requests.post(SERVER_URL + "/verify", json=req.model_dump())
output(req, Auth[ErrorResponse](**res.json()), res.status_code, 409)

assert res.json()["data"]["content"]["detail"] == "ticket is already stamped", (
    f"{repr(res.json()["data"]["content"]["detail"])} != 'ticket is already stamped'"
)

##########

print(
    "Realizing that his plan is most likely now foiled, Wesley performs " \
    "another verification request to see the status of Geordi's ticket.  " \
    "He should be able to see if it is redeemed, but he won't know whether " \
    "or not Geordi was stamped and admitted."
)

req = Auth[VerifyRequest].load(
    VerifyRequest(
        event_id=event_id_1,
        ticket=geordi_ticket,
        check_public_key=geordi.public_key
    ),
    wesley
)
res = requests.post(SERVER_URL + "/verify", json=req.model_dump())
output(req, Auth[VerifyResponse](**res.json()), res.status_code, 200)

assert res.json()["data"]["content"]["redeemed"] == True, (
    f"{repr(res.json()["data"]["content"]["redeemed"])} != True"
)
assert res.json()["data"]["content"]["stamped"] is None, (
    f"{repr(res.json()["data"]["content"]["stamped"])} is not None"
)
assert res.json()["data"]["content"]["version"] == 2, (
    f"{repr(res.json()["data"]["content"]["version"]) != 2}"
)
assert res.json()["data"]["content"]["transfer_limit"] == 63, (
    f"{repr(res.json()["data"]["content"]["transfer_limit"]) != 63}"
)
assert res.json()["data"]["content"]["metadata"] is None, (
    f"{repr(res.json()["data"]["content"]["metadata"])} is not None"
)

##########

print(
    "Furious at Wesley, but unable to find him, Beverly decides she is going " \
    "to attend the recital after all in an attempt to calm herself down.  " \
    "She calls up Geordi to ask for her ticket back, and he signs and sends "
    "her a transfer validation block.  She submits the request... but " \
    "doesn't know that Geordi's ticket has already been redeemed and stamped."
)

req = Auth[TransferRequest].load(
    TransferRequest(
        event_id=event_id_1,
        transfer=Auth[Transfer].load(
            Transfer(
                ticket=geordi_ticket,
                transfer_public_key=beverly.public_key
            ),
            geordi
        )
    ),
    beverly
)
res = requests.post(SERVER_URL + "/transfer", json=req.model_dump())
output(req, Auth[ErrorResponse](**res.json()), res.status_code, 409)

assert res.json()["data"]["content"]["detail"] == "ticket transfer failed", (
    f"{repr(res.json()["data"]["content"]["detail"])} != 'ticket transfer failed'"
)

##########

print(
    "Beverly is now livid at the situation, forcing Geordi to leave the " \
    "event to go and comfort her.  And upon his return, Geordi attempts to " \
    "re-redeem his ticket to streamline getting back inside before the show " \
    "starts."
)

req = Auth[RedeemRequest].load(
    RedeemRequest(
        event_id=event_id_1,
        ticket=geordi_ticket
    ),
    geordi
)
res = requests.post(SERVER_URL + "/redeem", json=req.model_dump())
output(req, Auth[ErrorResponse](**res.json()), res.status_code, 409)

assert res.json()["data"]["content"]["detail"] == "ticket redemption failed", (
    f"{repr(res.json()["data"]["content"]["detail"])} != 'ticket redemption failed'"
)

##########

print(
    "Meanwhile, Wesley has finally realized that instead of trying to steal " \
    "other people's tickets and credentials, he can simply register himself."
)

req = Auth[RegisterRequest].load(
    RegisterRequest(
        event_id=event_id_1
    ), 
    wesley
)
res = requests.post(SERVER_URL + "/register", json=req.model_dump())
output(req, Auth[RegisterResponse](**res.json()), res.status_code, 200)

wesley_ticket = res.json()["data"]["content"]["ticket"]
assert wesley_ticket is not None, "None is None"

##########

print(
    "Beverly finds out about her son's plan, takes a copy of his ticket " \
    "data/public key, and attempts to cancel his ticket."
)

req = Auth[CancelRequest].load(
    CancelRequest(
        event_id=event_id_1,
        ticket=wesley_ticket,
        check_public_key=wesley.public_key
    ),
    beverly
)
res = requests.post(SERVER_URL + "/cancel", json=req.model_dump())
output(req, Auth[ErrorResponse](**res.json()), res.status_code, 403)

assert res.json()["data"]["content"]["detail"] == "not event owner", (
    f"{repr(res.json()["data"]["content"]["detail"])} != 'not event owner'"
)

##########

print(
    "Unable to do it herself, she calls up Jean-Luc (the event owner) to " \
    "cancel the ticket."
)

req = Auth[CancelRequest].load(
    CancelRequest(
        event_id=event_id_1,
        ticket=wesley_ticket,
        check_public_key=wesley.public_key
    ),
    jean_luc
)
res = requests.post(SERVER_URL + "/cancel", json=req.model_dump())
output(req, Auth[CancelResponse](**res.json()), res.status_code, 200)

assert res.json()["data"]["content"]["success"] == True, (
    f"{repr(res.json()["data"]["content"]["success"])} != True"
)

##########

print("Wesley then tries to redeem his new ticket, not knowing it was canceled.")

req = Auth[RedeemRequest].load(
    RedeemRequest(
        event_id=event_id_1,
        ticket=wesley_ticket
    ),
    wesley
)
res = requests.post(SERVER_URL + "/redeem", json=req.model_dump())
output(req, Auth[ErrorResponse](**res.json()), res.status_code, 409)

assert res.json()["data"]["content"]["detail"] == "ticket canceled", (
    f"{repr(res.json()["data"]["content"]["detail"])} != 'ticket canceled'"
)

##########

print(
    "He wonders if initiating a transfer to himself to get a new encrypted " \
    "ticket ciphertext with a new ticket version would do any good."
)

req = Auth[TransferRequest].load(
    TransferRequest(
        event_id=event_id_1,
        transfer=Auth[Transfer].load(
            Transfer(
                ticket=wesley_ticket,
                transfer_public_key=wesley.public_key
            ),
            wesley
        )
    ),
    wesley
)
res = requests.post(SERVER_URL + "/transfer", json=req.model_dump())
output(req, Auth[ErrorResponse](**res.json()), res.status_code, 409)

assert res.json()["data"]["content"]["detail"] == "ticket canceled", (
    f"{repr(res.json()["data"]["content"]["detail"])} != 'ticket canceled'"
)

##########

print(
    "With one final trick up his sleeve... Wesley crafts up his best " \
    "disguise and shows up at the door to the event.  Wesley presents his " \
    "ticket to Jean-Luc, who attempts to stamp it."
)

req = Auth[VerifyRequest].load(
    VerifyRequest(
        event_id=event_id_1,
        ticket=wesley_ticket,
        check_public_key=wesley.public_key
    ),
    jean_luc
)
res = requests.post(SERVER_URL + "/verify", json=req.model_dump())
output(req, Auth[ErrorResponse](**res.json()), res.status_code, 409)

assert res.json()["data"]["content"]["detail"] == "ticket canceled", (
    f"{repr(res.json()["data"]["content"]["detail"])} != 'ticket canceled'"
)

##########

print(
    "William also plays an instrument, the trombone, and wants to have a " \
    'recital.  He creates an event: "Jazz Trombone" -- but marks it as ' \
    "\"restricted\" after hearing about Wesley's antics at the last recital..."
)

req = Auth[CreateRequest].load(
    CreateRequest(
        event=Event(
            name="Jazz Trombone",
            description="Any jazz except Dixieland",
            tickets=2,
            restricted=True,
            transfer_limit=1
        )
    ),
    william
)
res = requests.post(SERVER_URL + "/create", json=req.model_dump())

res_2 = requests.post(SERVER_URL + "/create", json=req.model_dump())
res_2_auth = Auth[ErrorResponse](**res_2.json())
res_2_auth.authenticate()
# run replay request to detect time-sensitive nonce repeat for the next test

output(req, Auth[CreateResponse](**res.json()), res.status_code, 200)

event_id_2 = res.json()["data"]["content"]["event_id"]
assert len(event_id_2) == 36, f"{len(event_id_2)} != 36"

##########

print(
    "Wesley still wants to wreak as much havoc as humanly possible, though, " \
    "so he interecepts and replays William's creation request."
)

output(req, res_2_auth, res_2.status_code, 409, auth=False)

assert res_2.json()["data"]["content"]["detail"] == "duplicate request nonce", (
    f"{repr(res_2.json()["data"]["content"]["detail"])} != 'duplicate request nonce'"
)

##########

print("He waits until the server forgets about the request nonce and tries again.")

req.data.timestamp -= TIMESTAMP_ERROR
res = requests.post(SERVER_URL + "/create", json=req.model_dump())
output(req, Auth[ErrorResponse](**res.json()), res.status_code, 400)
# timestamp error triggers before any other checks

assert res.json()["data"]["content"]["detail"] == "timestamp out of sync", (
    f"{repr(res.json()["data"]["content"]["detail"])} != 'timestamp out of sync'"
)

##########

print(
    "Finally, he makes one final attempt and alters the nonce and timestamp " \
    "data before making another request."
)

req.data.nonce = str(uuid.uuid4())
req.data.timestamp = time.time()
res = requests.post(SERVER_URL + "/create", json=req.model_dump())
output(req, Auth[ErrorResponse](**res.json()), res.status_code, 403)

assert res.json()["data"]["content"]["detail"] == "signature verification failed", (
    f"{repr(res.json()["data"]["content"]["detail"])} != 'signature verification failed'"
)

##########

print(
    "Wesley has a new idea now, though... he knows Jean-Luc's old event has " \
    "not yet been removed from the system, and so he registers a new ticket."
)

req = Auth[RegisterRequest].load(
    RegisterRequest(
        event_id=event_id_1
    ), 
    wesley
)
res = requests.post(SERVER_URL + "/register", json=req.model_dump())
output(req, Auth[RegisterResponse](**res.json()), res.status_code, 200)

wesley_ticket = res.json()["data"]["content"]["ticket"]
assert wesley_ticket is not None, "None is None"

##########

print("He then uses this ticket to try and redeem for William's new event.")

req = Auth[RedeemRequest].load(
    RedeemRequest(
        event_id=event_id_2,
        ticket=wesley_ticket
    ),
    wesley
)
res = requests.post(SERVER_URL + "/redeem", json=req.model_dump())
output(req, Auth[ErrorResponse](**res.json()), res.status_code, 403)

assert res.json()["data"]["content"]["detail"] == "ticket verification failed", (
    f"{repr(res.json()["data"]["content"]["detail"])} != 'ticket verification failed'"
)

##########

print(
    "Deanna, William's wife, also wants to attend the event.  She doesn't " \
    "know about the verification requirements, so she attempts to just " \
    "register without it."
)

req = Auth[RegisterRequest].load(
    RegisterRequest(
        event_id=event_id_2
    ), 
    deanna
)
res = requests.post(SERVER_URL + "/register", json=req.model_dump())
output(req, Auth[ErrorResponse](**res.json()), res.status_code, 403)

assert res.json()["data"]["content"]["detail"] == "verification required", (
    f"{repr(res.json()["data"]["content"]["detail"])} != 'verification required'"
)

##########

print(
    "William signs a registration verification block for Deanna, and he " \
    "includes custom metadata to be embedded into her ticket.  Deanna then " \
    "uses this to register for the event."
)

deanna_verification = Auth[Verification].load(
    Verification(
        event_id=event_id_2,
        public_key=deanna.public_key,
        transfer_limit=0,
        metadata="Imzadi <3"
    ),
    william
)

req = Auth[RegisterRequest].load(
    RegisterRequest(
        event_id=event_id_2,
        verification=deanna_verification
    ), 
    deanna
)
res = requests.post(SERVER_URL + "/register", json=req.model_dump())
output(req, Auth[RegisterResponse](**res.json()), res.status_code, 200)

deanna_ticket = res.json()["data"]["content"]["ticket"]
assert deanna_ticket is not None, "None is None"

##########

print(
    "Wesley intercepts this network traffic, however, and he attempts to " \
    "use Deanna's verification block to register a ticket for himself."
)

req = Auth[RegisterRequest].load(
    RegisterRequest(
        event_id=event_id_2,
        verification=deanna_verification
    ), 
    wesley
)
res = requests.post(SERVER_URL + "/register", json=req.model_dump())
output(req, Auth[ErrorResponse](**res.json()), res.status_code, 403)

assert res.json()["data"]["content"]["detail"] == "verification for different user", (
    f"{repr(res.json()["data"]["content"]["detail"])} != 'verification for different user'"
)

##########

print("Undeterred, he tries to sign his own verification block to register with...")

req = Auth[RegisterRequest].load(
    RegisterRequest(
        event_id=event_id_2,
        verification=Auth[Verification].load(
            Verification(
                event_id=event_id_2,
                public_key=wesley.public_key,
                metadata="Imzadi <3"
            ),
            wesley
        )
    ), 
    wesley
)
res = requests.post(SERVER_URL + "/register", json=req.model_dump())
output(req, Auth[ErrorResponse](**res.json()), res.status_code, 403)

assert res.json()["data"]["content"]["detail"] == "unauthorized signer", (
    f"{repr(res.json()["data"]["content"]["detail"])} != 'unauthorized signer'"
)

########## TODO - finish update and add wesley forged gen sig

print(
    '"What about if I spoof the signature?" he thinks -- and so he creates ' \
    "a request with a new verification block: signed by him but with " \
    "William's public key attached."
)

wesley_forged = AKC(private_key=wesley.private_key)
wesley_forged.public_key = william.public_key

req = Auth[RegisterRequest].load(
    RegisterRequest(
        event_id=event_id_2,
        verification=Auth[Verification].load(
            Verification(
                event_id=event_id_2,
                public_key=wesley.public_key,
                metadata="Imzadi <3"
            ),
            wesley_forged
        )
    ), 
    wesley
)
res = requests.post(SERVER_URL + "/register", json=req.model_dump())
output(req, Auth[ErrorResponse](**res.json()), res.status_code, 403)

assert res.json()["data"]["content"]["detail"] == "signature verification failed", (
    f"{repr(res.json()["data"]["content"]["detail"])} != 'signature verification failed'"
)

##########

print(
    "Deanna feels bad for Wesley and decides to transfer him her ticket, " \
    "but William is well-aware of her hyperempathetic nature and had " \
    "already set a customer ticket transfer limit of 0 for her."
)

req = Auth[TransferRequest].load(
    TransferRequest(
        event_id=event_id_2,
        transfer=Auth[Transfer].load(
            Transfer(
                ticket=deanna_ticket,
                transfer_public_key=wesley.public_key
            ),
            deanna
        )
    ),
    wesley
)
res = requests.post(SERVER_URL + "/transfer", json=req.model_dump())
output(req, Auth[ErrorResponse](**res.json()), res.status_code, 409)

assert res.json()["data"]["content"]["detail"] == "ticket transfer limit reached", (
    f"{repr(res.json()["data"]["content"]["detail"])} != 'ticket transfer limit reached'"
)

##########

print(
    "Meanwhile, William has given Beverly a legitamite verification block, " \
    "and she registers for the event -- claiming the last available ticket."
)

req = Auth[RegisterRequest].load(
    RegisterRequest(
        event_id=event_id_2,
        verification=Auth[Verification].load(
            Verification(
                event_id=event_id_2,
                public_key=beverly.public_key,
                metadata={
                    "mission": "to boldy go where no man has gone before",
                    "duration": 5
                }
            ),
            william
        )
    ), 
    beverly
)
res = requests.post(SERVER_URL + "/register", json=req.model_dump())
output(req, Auth[RegisterResponse](**res.json()), res.status_code, 200)

beverly_ticket = res.json()["data"]["content"]["ticket"]
assert beverly_ticket is not None, "None is None"

##########

print(
    "Beverly forgot the metadata that William injected into her ticket, so " \
    "she makes a /verify request to confirm it."
)

req = Auth[VerifyRequest].load(
    VerifyRequest(
        event_id=event_id_2,
        ticket=beverly_ticket,
        check_public_key=beverly.public_key
    ),
    beverly
)
res = requests.post(SERVER_URL + "/verify", json=req.model_dump())
output(req, Auth[VerifyResponse](**res.json()), res.status_code, 200)

assert res.json()["data"]["content"]["redeemed"] == False, (
    f"{repr(res.json()["data"]["content"]["redeemed"])} != True"
)
assert res.json()["data"]["content"]["stamped"] == False, (
    f"{repr(res.json()["data"]["content"]["stamped"])} != True"
)
assert res.json()["data"]["content"]["version"] == 1, (
    f"{repr(res.json()["data"]["content"]["version"]) != 1}"
)
assert res.json()["data"]["content"]["transfer_limit"] == 1, (
    f"{repr(res.json()["data"]["content"]["transfer_limit"]) != 1}"
)
assert res.json()["data"]["content"]["metadata"] == {
    "mission": "to boldy go where no man has gone before",
    "duration": 5
}, (
    repr(res.json()["data"]["content"]["metadata"]) + " != {" \
    "'mission': 'to boldy go where no man has gone before', " \
    "'duration': 5" \
    "}"
)

##########

print(
    "Beverly realizes that her son is on the loose causing mayhem again, " \
    "however, and so she decides to transfer her ticker for this event to " \
    "Geordi as well."
)

req = Auth[TransferRequest].load(
    TransferRequest(
        event_id=event_id_2,
        transfer=Auth[Transfer].load(
            Transfer(
                ticket=beverly_ticket,
                transfer_public_key=geordi.public_key
            ),
            beverly
        )
    ),
    geordi
)
res = requests.post(SERVER_URL + "/transfer", json=req.model_dump())
output(req, Auth[TransferResponse](**res.json()), res.status_code, 200)

geordi_ticket = res.json()["data"]["content"]["ticket"]
assert geordi_ticket is not None, "None is None"

##########

print(
    "Geordi feels bad for Beverly now, though, and decides that he will give " \
    "her back the ticket and deal with Wesley himself... unfortunately, " \
    "neither of them realize that the ticket transfer limit for the event " \
    "has already been reached."
)

req = Auth[TransferRequest].load(
    TransferRequest(
        event_id=event_id_2,
        transfer=Auth[Transfer].load(
            Transfer(
                ticket=geordi_ticket,
                transfer_public_key=beverly.public_key
            ),
            geordi
        )
    ),
    beverly
)
res = requests.post(SERVER_URL + "/transfer", json=req.model_dump())
output(req, Auth[ErrorResponse](**res.json()), res.status_code, 409)

assert res.json()["data"]["content"]["detail"] == "ticket transfer limit reached", (
    f"{repr(res.json()["data"]["content"]["detail"])} != 'ticket transfer limit reached'"
)

##########

print(
    "Wesley has had enough.  He breaks into William's office, steals his " \
    "credentials, and issues himself a valid registration verification " \
    "block.  He then attampets to register using this, unaware that the " \
    'recital is already "sold out."'
)

req = Auth[RegisterRequest].load(
    RegisterRequest(
        event_id=event_id_2,
        verification=Auth[Verification].load(
            Verification(
                event_id=event_id_2,
                public_key=wesley.public_key
            ),
            william
        )
    ), 
    wesley
)
res = requests.post(SERVER_URL + "/register", json=req.model_dump())
output(req, Auth[ErrorResponse](**res.json()), res.status_code, 409)

assert res.json()["data"]["content"]["detail"] == "unable to issue ticket", (
    f"{repr(res.json()["data"]["content"]["detail"])} != 'unable to issue ticket'"
)

##########

print("Showing up to the event, Deanna redeems her ticket.")

req = Auth[RedeemRequest].load(
    RedeemRequest(
        event_id=event_id_2,
        ticket=deanna_ticket
    ),
    deanna
)
res = requests.post(SERVER_URL + "/redeem", json=req.model_dump())
output(req, Auth[RedeemResponse](**res.json()), res.status_code, 200)

assert res.json()["data"]["content"]["success"] == True, (
    f"{repr(res.json()["data"]["content"]["success"])} != True"
)

##########

print(
    "William verifies and stamps her ticket to confirm admittance, and he " \
    "can see the custom metadata that he had set earlier."
)

req = Auth[VerifyRequest].load(
    VerifyRequest(
        event_id=event_id_2,
        ticket=deanna_ticket,
        check_public_key=deanna.public_key,
        stamp=True
    ),
    william
)
res = requests.post(SERVER_URL + "/verify", json=req.model_dump())
output(req, Auth[VerifyResponse](**res.json()), res.status_code, 200)

assert res.json()["data"]["content"]["redeemed"] == True, (
    f"{repr(res.json()["data"]["content"]["redeemed"])} != True"
)
assert res.json()["data"]["content"]["stamped"] == True, (
    f"{repr(res.json()["data"]["content"]["stamped"])} != True"
)
assert res.json()["data"]["content"]["version"] == 1, (
    f"{repr(res.json()["data"]["content"]["version"]) != 1}"
)
assert res.json()["data"]["content"]["transfer_limit"] == 0, (
    f"{repr(res.json()["data"]["content"]["transfer_limit"]) != 0}"
)
assert res.json()["data"]["content"]["metadata"] == "Imzadi <3", (
    f"{repr(res.json()["data"]["content"]["metadata"])} != 'Imzadi <3'"
)

##########

print(
    "Deanna wants to see her ticket state data again and asks William to " \
    "make another verify request to show her (no stamp)."
)

req = Auth[VerifyRequest].load(
    VerifyRequest(
        event_id=event_id_2,
        ticket=deanna_ticket,
        check_public_key=deanna.public_key
    ),
    william
)
res = requests.post(SERVER_URL + "/verify", json=req.model_dump())
output(req, Auth[VerifyResponse](**res.json()), res.status_code, 200)

assert res.json()["data"]["content"]["redeemed"] == True, (
    f"{repr(res.json()["data"]["content"]["redeemed"])} != True"
)
assert res.json()["data"]["content"]["stamped"] == True, (
    f"{repr(res.json()["data"]["content"]["stamped"])} != True"
)
assert res.json()["data"]["content"]["version"] == 1, (
    f"{repr(res.json()["data"]["content"]["version"]) != 1}"
)
assert res.json()["data"]["content"]["transfer_limit"] == 0, (
    f"{repr(res.json()["data"]["content"]["transfer_limit"]) != 0}"
)
assert res.json()["data"]["content"]["metadata"] == "Imzadi <3", (
    f"{repr(res.json()["data"]["content"]["metadata"])} != 'Imzadi <3'"
)

##########

print(
    "But, oh no... Jean-Luc just called William to deal with an impending " \
    "emergency, and he has to cancel his event.  He quickly makes the " \
    "deletion request before heading off to handle the problem."
)

req = Auth[DeleteRequest].load(
    DeleteRequest(
        event_id=event_id_2
    ),
    william
)
res = requests.post(SERVER_URL + "/delete", json=req.model_dump())
output(req, Auth[DeleteResponse](**res.json()), res.status_code, 200)

assert res.json()["data"]["content"]["success"] == True, (
    f"{repr(res.json()["data"]["content"]["success"])} != True"
)

##########

print(
    "Geordi didn't hear about any emergency, though, and so he attempts to " \
    "redeem his ticket as normal."
)

req = Auth[RedeemRequest].load(
    RedeemRequest(
        event_id=event_id_2,
        ticket=geordi_ticket
    ),
    geordi
)
res = requests.post(SERVER_URL + "/redeem", json=req.model_dump())
output(req, Auth[ErrorResponse](**res.json()), res.status_code, 404)

assert res.json()["data"]["content"]["detail"] == "event not found", (
    f"{repr(res.json()["data"]["content"]["detail"])} != 'event not found'"
)

##########

print(
    "After dealing with the emergecy, William gets back to his office and " \
    'decides to do some "spring cleaning" -- making a requets to delete ' \
    "Jean-Luc's old event from the server."
)

req = Auth[DeleteRequest].load(
    DeleteRequest(
        event_id=event_id_1
    ),
    william
)
res = requests.post(SERVER_URL + "/delete", json=req.model_dump())
output(req, Auth[ErrorResponse](**res.json()), res.status_code, 403)

assert res.json()["data"]["content"]["detail"] == "not event owner", (
    f"{repr(res.json()["data"]["content"]["detail"])} != 'not event owner'"
)

##########

print("William calls up Jean-Luc, and he then makes the deletion request for his event.")

req = Auth[DeleteRequest].load(
    DeleteRequest(
        event_id=event_id_1
    ),
    jean_luc
)
res = requests.post(SERVER_URL + "/delete", json=req.model_dump())
output(req, Auth[DeleteResponse](**res.json()), res.status_code, 200)

assert res.json()["data"]["content"]["success"] == True, (
    f"{repr(res.json()["data"]["content"]["success"])} != True"
)

##########

print(
    "Wesley is exhausted at this point, but decides to search for William's " \
    "event to see if he can figure out what the heck is even going on."
)

req = Auth[SearchRequest].load(
    SearchRequest(
        text=event_id_2,
        mode="id"
    ),
    wesley
)
res = requests.post(SERVER_URL + "/search", json=req.model_dump())
output(req, Auth[ErrorResponse](**res.json()), res.status_code, 404)

assert res.json()["data"]["content"]["detail"] == "event not found", (
    f"{repr(res.json()["data"]["content"]["detail"])} != 'event not found'"
)

##########

print("Maybe Jean-Luc's event is still there, though, he thinks?")

req = Auth[SearchRequest].load(
    SearchRequest(
        text=event_id_1,
        mode="id"
    ),
    wesley
)
res = requests.post(SERVER_URL + "/search", json=req.model_dump())
output(req, Auth[ErrorResponse](**res.json()), res.status_code, 404)

assert res.json()["data"]["content"]["detail"] == "event not found", (
    f"{repr(res.json()["data"]["content"]["detail"])} != 'event not found'"
)

##########

print("Wesley gives up and goes to bed.")
print("The end.")