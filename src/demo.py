"""
Demo/testing module.

:author: Max Milazzo
"""



from app.API.models.base import Auth, Error
from app.API.models.endpoints import *
from app.API.models.endpoints.register import Verification
from app.API.models.endpoints.transfer import Transfer
from app.data.models.event import Event
from app.crypto.asymmetric import AKC
from app.util import display

import time
import uuid
import copy
import requests
from typing import TypeVar



SERVER_URL = "http://localhost:8000"
# server URL


TIMESTAMP_ERROR = 10
# timestamp error allowance for response


T = TypeVar("T")



def output(req: dict, res: Auth[T], code: int) -> None:
    """
    Compact request/response logging with STATUS first and an auth verdict.
    """

    res.authenticate()
    
    print("====================")
    print(f"STATUS: {code}")
    print("\nREQUEST:", req)
    print("\nRESPONSE:", res.model_dump())
    print()

    input("> ")
    print()


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
            restricted=False
        )
    ),
    jean_luc.private_key,
    jean_luc.public_key
).model_dump()
res = requests.post(SERVER_URL + "/create", json=req)
output(req, Auth[CreateResponse](**res.json()), res.status_code)

event_id = res.json()["data"]["content"]["event_id"]

##########

print("Beverly wants to see him play, so she searches for the event.")

req = Auth[SearchRequest].load(
    SearchRequest(
        text="flute",
        mode="text"
    ),
    beverly.private_key,
    beverly.public_key
).model_dump()
res = requests.post(SERVER_URL + "/search", json=req)
output(req, Auth[SearchResponse](**res.json()), res.status_code)

##########

print("And now that she has the event ID, she registers for the recital.")

req = Auth[RegisterRequest].load(
    RegisterRequest(
        event_id=event_id
    ), 
    beverly.private_key,
    beverly.public_key
).model_dump()
res = requests.post(SERVER_URL + "/register", json=req)
output(req, Auth[RegisterResponse](**res.json()), res.status_code)

beverly_ticket = res.json()["data"]["content"]["ticket"]

##########

print(
    "Berverly's son Wesley wants to attend too, but he is currently grounded "
    "for covering up his former classmate's death.  He's not going to let " \
    "that stop him, though, and so he tries to submit a forged request to " \
    "transfer his mom's ticket to him."
)

req = Auth[TransferRequest].load(
    TransferRequest(
        event_id=event_id,
        transfer=Auth[Transfer].load(
            Transfer(
                ticket=beverly_ticket,
                transfer_public_key=wesley.public_key
            ),
            wesley.private_key,
            beverly.public_key
        )
    ),
    wesley.private_key,
    wesley.public_key
).model_dump()
res = requests.post(SERVER_URL + "/transfer", json=req)
output(req, Auth[Error](**res.json()), res.status_code)

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
        event_id=event_id,
        transfer=Auth[Transfer].load(
            Transfer(
                ticket=beverly_ticket,
                transfer_public_key=geordi.public_key
            ),
            beverly.private_key,
            beverly.public_key
        )
    ),
    geordi.private_key,
    geordi.public_key
).model_dump()
res = requests.post(SERVER_URL + "/transfer", json=req)
output(req, Auth[TransferResponse](**res.json()), res.status_code)

geordi_ticket = res.json()["data"]["content"]["ticket"]

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
        event_id=event_id,
        ticket=beverly_ticket
    ),
    beverly.private_key,
    beverly.public_key
).model_dump()
res = requests.post(SERVER_URL + "/redeem", json=req)
output(req, Auth[Error](**res.json()), res.status_code)

##########

print(
    "Still not ready to concede, Wesley comes up with a new ingenious plan: " \
    "He will simply transfer his mom's non-functional ticket to himself, " \
    "and then surely everything will work for him."
)

req = Auth[TransferRequest].load(
    TransferRequest(
        event_id=event_id,
        transfer=Auth[Transfer].load(
            Transfer(
                ticket=beverly_ticket,
                transfer_public_key=wesley.public_key
            ),
            beverly.private_key,
            beverly.public_key
        )
    ),
    wesley.private_key,
    wesley.public_key
).model_dump()
res = requests.post(SERVER_URL + "/transfer", json=req)
output(req, Auth[Error](**res.json()), res.status_code)


##########

print(
    "A bit frustrated now, he sees Geordi about to enter the recital.  " \
    "He quickly steals a copy of Geordi's ticket and public key to check if " \
    "it has already been redeemed.  This endpoint is available to all users " \
    "to promote transfer transparency... but Wesley plans to use it for evil!"
)

req = Auth[VerifyRequest].load(
    VerifyRequest(
        event_id=event_id,
        ticket=geordi_ticket,
        check_public_key=geordi.public_key
    ),
    wesley.private_key,
    wesley.public_key
).model_dump()
res = requests.post(SERVER_URL + "/verify", json=req)
output(req, Auth[VerifyResponse](**res.json()), res.status_code)

##########

# Jean-Luc attempts to redeem for Geordi
print(
    "Upon seeing Geordi, Jean-Luc gets so excited that he takes Geordi's " \
    "ticket and tries to make a redemption request for him."
)

req = Auth[RedeemRequest].load(
    RedeemRequest(
        event_id=event_id,
        ticket=geordi_ticket
    ),
    jean_luc.private_key,
    jean_luc.public_key
).model_dump()
res = requests.post(SERVER_URL + "/redeem", json=req)
output(req, Auth[Error](**res.json()), res.status_code)

##########

# Jean-Luc tries to skip redeem and just stamp Geordi's ticket
print(
    '"No matter," he thinks; he will simply skip redemption and proceed to ' \
    "ticket verification and stamping.  So Jean-Luc makes a verification/" \
    "stamping request in an attempt to confirm and mark Geordi as admitted."
)

req = Auth[VerifyRequest].load(
    VerifyRequest(
        event_id=event_id,
        ticket=geordi_ticket,
        check_public_key=geordi.public_key,
        stamp=True
    ),
    jean_luc.private_key,
    jean_luc.public_key
).model_dump()
res = requests.post(SERVER_URL + "/verify", json=req)
output(req, Auth[Error](**res.json()), res.status_code)

##########

# Geoerdi tries to redeem, but Wesley messes up ticket ciphertext bits
print(
    "Geordi finally makes the redemption request himself... however, Wesley " \
    "attempts to jam the signal, and the request reaches the server with a " \
    "few of the encrypted ticket ciphertext bytes mixed up."
)

bad_ticket = geordi_ticket[:-1] + ("A" if geordi_ticket[-1] != "A" else "B")

req = Auth[RedeemRequest].load(
    RedeemRequest(
        event_id=event_id,
        ticket=bad_ticket
    ),
    geordi.private_key,
    geordi.public_key
).model_dump()
res = requests.post(SERVER_URL + "/redeem", json=req)
output(req, Auth[Error](**res.json()), res.status_code)

##########

# Geordi redeems for himself
print(
    "Unsure what had just happened, Geordi retries the redemption.  And " \
    "thankfully for him, Wesley's signal jammer just ran out of power, " \
    "so his request reaches the server unaltered."
)

req = Auth[RedeemRequest].load(
    RedeemRequest(
        event_id=event_id,
        ticket=geordi_ticket
    ),
    geordi.private_key,
    geordi.public_key
).model_dump()
res = requests.post(SERVER_URL + "/redeem", json=req)
output(req, Auth[RedeemResponse](**res.json()), res.status_code)

##########

# Now Geordi attempts to stamp his own ticket (which fails obviously)
print("Without thinking, Geordi then attempts to stamp his own ticket.")

req = Auth[VerifyRequest].load(
    VerifyRequest(
        event_id=event_id,
        ticket=geordi_ticket,
        check_public_key=geordi.public_key,
        stamp=True
    ),
    geordi.private_key,
    geordi.public_key
).model_dump()
res = requests.post(SERVER_URL + "/verify", json=req)
output(req, Auth[Error](**res.json()), res.status_code)

##########

# Jean-Luc verifies with stamp
print("Finally, Jean-Luc sends a proper verify/stamp request to admit Geordi")

req = Auth[VerifyRequest].load(
    VerifyRequest(
        event_id=event_id,
        ticket=geordi_ticket,
        check_public_key=geordi.public_key,
        stamp=True
    ),
    jean_luc.private_key,
    jean_luc.public_key
).model_dump()
res = requests.post(SERVER_URL + "/verify", json=req)
output(req, Auth[VerifyResponse](**res.json()), res.status_code)

##########

# Jean-Luc stamps again, with a failure message that the ticket is already stamped
print("...And just to make sure, he stamps it for a second time too!")

req = Auth[VerifyRequest].load(
    VerifyRequest(
        event_id=event_id,
        ticket=geordi_ticket,
        check_public_key=geordi.public_key,
        stamp=True
    ),
    jean_luc.private_key,
    jean_luc.public_key
).model_dump()
res = requests.post(SERVER_URL + "/verify", json=req)
output(req, Auth[Error](**res.json()), res.status_code)

##########

# Wesley does /verify again and see if ticket has been redeemed
print(
    "Realizing that his plan is most likely now foiled, Wesley performs " \
    "another verification request to see the status of Geordi's ticket.  " \
    "He should be able to see if it is redeemed, but he won't know whether " \
    "or not Geordi was stamped and admitted."
)

req = Auth[VerifyRequest].load(
    VerifyRequest(
        event_id=event_id,
        ticket=geordi_ticket,
        check_public_key=geordi.public_key
    ),
    wesley.private_key,
    wesley.public_key
).model_dump()
res = requests.post(SERVER_URL + "/verify", json=req)
output(req, Auth[VerifyResponse](**res.json()), res.status_code)

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
        event_id=event_id,
        transfer=Auth[Transfer].load(
            Transfer(
                ticket=geordi_ticket,
                transfer_public_key=beverly.public_key
            ),
            geordi.private_key,
            geordi.public_key
        )
    ),
    beverly.private_key,
    beverly.public_key
).model_dump()
res = requests.post(SERVER_URL + "/transfer", json=req)
output(req, Auth[Error](**res.json()), res.status_code)

##########

print(
    "Beverly is now livid at the situation, forcing Geordi to leave the " \
    "event to go and comfort her.  And upon his return, Geordi attempts to " \
    "re-redeem his ticket to streamline getting back inside before the show " \
    "starts."
)

req = Auth[RedeemRequest].load(
    RedeemRequest(
        event_id=event_id,
        ticket=geordi_ticket
    ),
    geordi.private_key,
    geordi.public_key
).model_dump()
res = requests.post(SERVER_URL + "/redeem", json=req)
output(req, Auth[Error](**res.json()), res.status_code)

##########

print(
    "Meanwhile, Wesley has finally realized that instead of trying to steal " \
    "other people's tickets and credentials, he can simply register himself."
)

req = Auth[RegisterRequest].load(
    RegisterRequest(
        event_id=event_id
    ), 
    wesley.private_key,
    wesley.public_key
).model_dump()
res = requests.post(SERVER_URL + "/register", json=req)
output(req, Auth[RegisterResponse](**res.json()), res.status_code)

wesley_ticket = res.json()["data"]["content"]["ticket"]

##########

# Beverly tries to cancel his ticket
print(
    "Beverly finds out about her son's plan, takes a copy of his ticket " \
    "data/public key, and attempts to cancel his ticket."
)

req = Auth[CancelRequest].load(
    CancelRequest(
        event_id=event_id,
        ticket=wesley_ticket,
        check_public_key=wesley.public_key
    ),
    beverly.private_key,
    beverly.public_key
).model_dump()
res = requests.post(SERVER_URL + "/cancel", json=req)
output(req, Auth[Error](**res.json()), res.status_code)

##########

# She tells Jean-Luc and he cancels it when he shows up at the event
print(
    "Unable to do it herself, she calls up Jean-Luc (the event owner) to " \
    "cancel the ticket."
)

req = Auth[CancelRequest].load(
    CancelRequest(
        event_id=event_id,
        ticket=wesley_ticket,
        check_public_key=wesley.public_key
    ),
    jean_luc.private_key,
    jean_luc.public_key
).model_dump()
res = requests.post(SERVER_URL + "/cancel", json=req)
output(req, Auth[CancelResponse](**res.json()), res.status_code)

##########

# Wesley attempts to redeem and transfer
print("Wesley then tries to redeem his new ticket, not knowing it was canceled.")

req = Auth[RedeemRequest].load(
    RedeemRequest(
        event_id=event_id,
        ticket=wesley_ticket
    ),
    wesley.private_key,
    wesley.public_key
).model_dump()
res = requests.post(SERVER_URL + "/redeem", json=req)
output(req, Auth[Error](**res.json()), res.status_code)

##########

print(
    "He wonders if initiating a transfer to himself to get a new encrypted " \
    "ticket ciphertext with a new ticket version would do any good."
)

req = Auth[TransferRequest].load(
    TransferRequest(
        event_id=event_id,
        transfer=Auth[Transfer].load(
            Transfer(
                ticket=wesley_ticket,
                transfer_public_key=wesley.public_key
            ),
            wesley.private_key,
            wesley.public_key
        )
    ),
    wesley.private_key,
    wesley.public_key
).model_dump()
res = requests.post(SERVER_URL + "/transfer", json=req)
output(req, Auth[Error](**res.json()), res.status_code)

##########

# Wesley dresses up in a disguise and asks Jean-Luc to stamp his ticket -- which fails
print(
    "With one final trick up his sleeve... Wesley crafts up his best " \
    "disguise and shows up at the door to the event.  Wesley presents his " \
    "ticket to Jean-Luc, who attempts to stamp it."
)

req = Auth[VerifyRequest].load(
    VerifyRequest(
        event_id=event_id,
        ticket=wesley_ticket,
        check_public_key=wesley.public_key
    ),
    jean_luc.private_key,
    jean_luc.public_key
).model_dump()
res = requests.post(SERVER_URL + "/verify", json=req)
output(req, Auth[Error](**res.json()), res.status_code)


"""
# =========================== ACT II ===========================
display.clear()
print("ACT II — Restricted session with verification blocks, replay/tamper/expiry, and sold-out behavior.")
input("> Continue… ")

dea = AKC(); deanna_priv, deanna_pub = dea.private_key, dea.public_key
will = AKC(); will_priv, will_pub   = will.private_key, will.public_key
reg  = AKC(); reg_priv,  reg_pub    = reg.private_key,  reg.public_key
wes  = AKC(); wes_priv,  wes_pub    = wes.private_key,  wes.public_key

evt = Event(
    name="Counseling Session",
    description="Closed group.",
    tickets=2,
    start=time.time(),
    finish=time.time() + 2_628_000,
    restricted=True
)

# Create restricted event
print("Deanna creates a restricted session; she admits people selectively.")
req = auth_req(CreateRequest(event=evt), deanna_priv, deanna_pub, CreateRequest).model_dump()
res = requests.post(SERVER_URL + "/create", json=req); rcreate = parse_res(res)
show_req_res("Create Restricted Event (Deanna)", req, rcreate)
counsel_id = rcreate["data"]["content"]["event_id"]

# Cross-event misuse: try to use Tea Party ticket against Counseling event  [COVERAGE #7]
print("Try to use a Tea Party ticket against the Counseling event — wrong event should fail.")
req = auth_req(RedeemRequest(event_id=counsel_id, ticket=geordi_ticket),
               geor_priv, geor_pub, RedeemRequest).model_dump()
res = requests.post(SERVER_URL + "/redeem", json=req); cross_evt = parse_res(res)
show_req_res("Redeem with ticket for different event — expect FAIL", req, cross_evt)

# Replay same signed create — should fail (nonce replay)
print("Exact replay of the signed create to confirm nonce replay protection.")
res = requests.post(SERVER_URL + "/create", json=req); replay = parse_res(res)
show_req_res("Replay same signed /create — FAIL", req, replay)

# Expired timestamp
print("Expired timestamp attempt to verify freshness enforcement.")
req_stale = copy.deepcopy(req); req_stale["data"]["timestamp"] -= (TIMESTAMP_ERROR + 1)
res = requests.post(SERVER_URL + "/create", json=req_stale); stale = parse_res(res)
show_req_res("Expired timestamp /create — FAIL", req_stale, stale)

# Tamper after signature
print("Tampered payload (nonce changed after signing) to confirm signature binding.")
req_tamper = copy.deepcopy(req); req_tamper["data"]["nonce"] = str(uuid.uuid4()); req_tamper["data"]["timestamp"] = time.time()
res = requests.post(SERVER_URL + "/create", json=req_tamper); tamp = parse_res(res)
show_req_res("Tampered /create — FAIL", req_tamper, tamp)

# William tries to register without verification — fail
print("William tries to register without a verification block to confirm restriction is enforced.")
req = auth_req(RegisterRequest(event_id=counsel_id), will_priv, will_pub, RegisterRequest).model_dump()
res = requests.post(SERVER_URL + "/register", json=req); w_fail = parse_res(res)
show_req_res("Restricted register WITHOUT verification — FAIL (William)", req, w_fail)

# Deanna creates a verification block for William; display note
print("Deanna issues a verification block for William because she trusts his judgment.")
v_will = auth_req(Verification(event_id=counsel_id, public_key=will_pub, metadata="approved"),
                  deanna_priv, deanna_pub, Verification)
print("REGISTRATION VERIFICATION BLOCK: signed by owner, authorizing registrant (omitted details).")

# William registers with verification — success
print("William registers with the owner’s verification, proving the allow-list works.")
req = auth_req(RegisterRequest(event_id=counsel_id, verification=v_will),
               will_priv, will_pub, RegisterRequest).model_dump()
res = requests.post(SERVER_URL + "/register", json=req); w_ok = parse_res(res)
show_req_res("Restricted register WITH verification — SUCCESS (William)", req, w_ok)
will_ticket = w_ok["data"]["content"]["ticket"]

# Spoofed VERIFICATION signature (should fail)
print("An attacker spoofs the owner's signature on a verification block; registration must be rejected.")
# Create a block with the correct shape (owner/William), but replace its signature with one from the wrong key
v_template = v_will  # correct shape: owner authorizes William
v_wrong_sig = auth_req(
    Verification(event_id=counsel_id, public_key=will_pub, metadata="approved"),
    rand_priv, rand_pub, Verification
)

v_spoof = v_template.model_dump()
v_spoof["signature"] = v_wrong_sig.signature  # keep owner's public_key in the block, but wrong signature
v_spoof["data"]["nonce"] = str(uuid.uuid4())
v_spoof["data"]["timestamp"] = time.time()

req = auth_req(
    RegisterRequest(event_id=counsel_id, verification=v_spoof),
    will_priv, will_pub, RegisterRequest
).model_dump()
res = requests.post(SERVER_URL + "/register", json=req)
w_spoof = parse_res(res)
show_req_res("Restricted register with SPOOFED owner signature — FAIL (William)", req, w_spoof)

# Reginald tries using a block tied to William’s key — fail
print("Reginald attempts to reuse a block tied to William’s key to confirm key-binding is honored.")
v_wrong = auth_req(Verification(event_id=counsel_id, public_key=will_pub, metadata="wrong-key"),
                   deanna_priv, deanna_pub, Verification)
req = auth_req(RegisterRequest(event_id=counsel_id, verification=v_wrong),
               reg_priv, reg_pub, RegisterRequest).model_dump()
res = requests.post(SERVER_URL + "/register", json=req); rw = parse_res(res)
show_req_res("Restricted register with WRONG-key verification — FAIL (Reginald)", req, rw)

# Correct verification for Reginald — success
print("Deanna issues a new verification block for Reginald that matches his key.")
v_reg = auth_req(Verification(event_id=counsel_id, public_key=reg_pub),
                 deanna_priv, deanna_pub, Verification)
print("REGISTRATION VERIFICATION BLOCK: valid for Reginald (omitted details).")
req = auth_req(RegisterRequest(event_id=counsel_id, verification=v_reg),
               reg_priv, reg_pub, RegisterRequest).model_dump()
res = requests.post(SERVER_URL + "/register", json=req); r_ok = parse_res(res)
show_req_res("Restricted register WITH verification — SUCCESS (Reginald)", req, r_ok)
reg_ticket = r_ok["data"]["content"]["ticket"]

# Sold-out: Wesley has valid verification but event is full — should fail
print("Wesley arrives late with a valid verification, but capacity is already reached.")
v_wes = auth_req(Verification(event_id=counsel_id, public_key=wes_pub, metadata="ok"),
                 deanna_priv, deanna_pub, Verification)
print("REGISTRATION VERIFICATION BLOCK: valid for Wesley (omitted details).")
req = auth_req(RegisterRequest(event_id=counsel_id, verification=v_wes),
               wes_priv, wes_pub, RegisterRequest).model_dump()
res = requests.post(SERVER_URL + "/register", json=req); wes_fail = parse_res(res)
show_req_res("Restricted register SOLD OUT — FAIL (Wesley)", req, wes_fail)

# Normal flow for both tickets: owner verify(no stamp) → holder redeem → owner stamp
for who, w_priv, w_pub, ticket in [
    ("Reginald", reg_priv, reg_pub, reg_ticket),
    ("William",  will_priv, will_pub, will_ticket),
]:
    print(f"Owner verifies {who} without stamping (optional pre-check).")
    req = auth_req(VerifyRequest(event_id=counsel_id, ticket=ticket, check_public_key=w_pub),
                   deanna_priv, deanna_pub, VerifyRequest).model_dump()
    res = requests.post(SERVER_URL + "/verify", json=req); pv = parse_res(res)
    show_req_res(f"Owner Verify (no stamp) — {who}", req, pv)

    print(f"{who} redeems their ticket; holder’s signature proves possession.")
    req = auth_req(RedeemRequest(event_id=counsel_id, ticket=ticket),
                   w_priv, w_pub, RedeemRequest).model_dump()
    res = requests.post(SERVER_URL + "/redeem", json=req); red = parse_res(res)
    show_req_res(f"Redeem — {who}", req, red)

    print(f"Owner stamps {who}'s ticket after redemption; this prevents repeat use.")
    req = auth_req(VerifyRequest(event_id=counsel_id, ticket=ticket, check_public_key=w_pub, stamp=True),
                   deanna_priv, deanna_pub, VerifyRequest).model_dump()
    res = requests.post(SERVER_URL + "/verify", json=req); st = parse_res(res)
    show_req_res(f"Owner STAMP — {who}", req, st)

    # Owner re-verify sees stamp
    print(f"Owner re-verifies {who}'s ticket without stamping, confirming stamped state is recorded.")
    req = auth_req(
        VerifyRequest(event_id=counsel_id, ticket=ticket, check_public_key=w_pub, stamp=False),
        deanna_priv, deanna_pub, VerifyRequest
    ).model_dump()
    res = requests.post(SERVER_URL + "/verify", json=req); vs_owner = parse_res(res)
    show_req_res(f"Owner Verify AFTER Stamp (no-stamp flag) — {who}", req, vs_owner)

    # Non-owner re-verify does NOT see stamp
    print(f"A non-owner verifies {who}'s ticket and should NOT see stamped state.")
    req = auth_req(
        VerifyRequest(event_id=counsel_id, ticket=ticket, check_public_key=w_pub, stamp=False),
        rand_priv, rand_pub, VerifyRequest
    ).model_dump()
    res = requests.post(SERVER_URL + "/verify", json=req); vs_non_owner = parse_res(res)
    show_req_res(f"Non-owner Verify AFTER Stamp (no-stamp flag) — {who}", req, vs_non_owner)

# Deletion behavior
print("Deanna checks that the event exists by ID, then deletes it, then confirms it’s gone.")
req = auth_req(SearchRequest(text=counsel_id, mode="id"),
               deanna_priv, deanna_pub, SearchRequest).model_dump()
res = requests.post(SERVER_URL + "/search", json=req); s1 = parse_res(res)
show_req_res("Search by ID BEFORE delete (exists)", req, s1)

req = auth_req(DeleteRequest(event_id=counsel_id),
               deanna_priv, deanna_pub, DeleteRequest).model_dump()
res = requests.post(SERVER_URL + "/delete", json=req); dd = parse_res(res)
show_req_res("Delete event (Deanna)", req, dd)

req = auth_req(SearchRequest(text=counsel_id, mode="id"),
               deanna_priv, deanna_pub, SearchRequest).model_dump()
res = requests.post(SERVER_URL + "/search", json=req); s2 = parse_res(res)
show_req_res("Search by ID AFTER delete (gone)", req, s2)

print("\nTHE END — Demo complete.\n")
"""