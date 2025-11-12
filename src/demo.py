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

print("ZETA Demo (Condensed Story Mode)")
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

"""
##########

# Wesley does /verify to see if there is anyone who hasn't redeemed (explain why it exists)
print(
    "A bit frustrated now, he sees Geordi about to enter the recital.  " \
    "He quickly steals a copy of Geordi's ticket and public key to check if " \
    "it has already been redeemed.  This endpoint is available to all users " \
    "to promote transfer transparency... but Wesley plans to use it for evil!"
)

# Jean-Luc attempts to redeem for Geordi
print(
    "Upon seeing Geordi, Jean-Luc gets so excited that he takes Geordi's " \
    "ticket and tries to make a redemption request for him."
)

# Jean-Luc tries to skip redeem and just stamp Geordi's ticket
print(
    '"No matter," he thinks; he will simply skip redemption and proceed to ' \
    "ticket verification and stamping.  So Jean-Luc makes a verification/" \
    "stamping request in an attempt to confirm and mark Geordi as admitted."
)

# Geoerdi tries to redeem, but Wesley messes up ticket ciphertext bits
print(
    "Geordi finally makes the redemption request himself... however, Wesley " \
    "attempts to jam the signal, and the request reaches the server with a " \
    "few of the encrypted ticket ciphertext bytes mixed up."
)

# Geordi redeems for himself
print(
    "Unsure what had just happened, Geordi retries the redemption.  And " \
    "thankfully for him, Wesley's signal jammer just ran out of power, " \
    "so his request reaches the server unaltered."
)

# Now Geordi attempts to stamp his own ticket (which fails obviously)
print("Without thinking, Geordi then attempts to stamp his own ticket.")

# Jean-Luc verifies with stamp
print("Finally, Jean-Luc sends a proper verify/stamp request to admit Geordi")

# Jean-Luc stamps again, with a failure message that the ticket is already stamped
print("...And just to make sure, he stamps it for a second time too!")

# Wesley does /verify again and see if ticket has been redeemed
print(
    "Realizing that his plan is most likely now foiled, Wesley performs " \
    "another verification request to see the status of Geordi's ticket.  " \
    "He should be able to see if it is redeemed, but he won't know whether " \
    "or not Geordi was stamped and admitted."
)





# (Testing-only) Owner verify BEFORE redemption — not needed in real flow
print("Beverly performs a pre-redeem verify for testing; in practice stamping later is enough to prevent reuse.")
req = auth_req(VerifyRequest(event_id=event_id, ticket=geordi_ticket, check_public_key=geor_pub),
               beverly_priv, beverly_pub, VerifyRequest).model_dump()
res = requests.post(SERVER_URL + "/verify", json=req); v_before = parse_res(res)
show_req_res("Owner Verify BEFORE Redeem (optional)", req, v_before)

# Non-owner verify (read-only)
print("A non-owner does a verify-only check to confirm the ticket’s current state without any stamp authority.")
req = auth_req(VerifyRequest(event_id=event_id, ticket=geordi_ticket, check_public_key=geor_pub),
               rand_priv, rand_pub, VerifyRequest).model_dump()
res = requests.post(SERVER_URL + "/verify", json=req); v_non_owner = parse_res(res)
show_req_res("Verify by NON-OWNER (read-only; no stamp)", req, v_non_owner)

# Owner attempts to redeem on behalf of holder — should fail
print("Beverly attempts to redeem on Geordi’s behalf; the system should require the holder’s signature.")
req = auth_req(RedeemRequest(event_id=event_id, ticket=geordi_ticket),
               beverly_priv, beverly_pub, RedeemRequest).model_dump()
res = requests.post(SERVER_URL + "/redeem", json=req); orf = parse_res(res)
show_req_res("Owner tries to redeem FOR holder — expect FAIL", req, orf)

# Attempt to stamp BEFORE redemption — should fail  [COVERAGE #1]
print("Beverly attempts to stamp the ticket BEFORE redemption — should fail.")
req = auth_req(
    VerifyRequest(event_id=event_id, ticket=geordi_ticket, check_public_key=geor_pub, stamp=True),
    beverly_priv, beverly_pub, VerifyRequest
).model_dump()
res = requests.post(SERVER_URL + "/verify", json=req); bad_stamp = parse_res(res)
show_req_res("Owner STAMP BEFORE Redeem — expect FAIL", req, bad_stamp)

# Tamper ticket ciphertext — should fail integrity check  [COVERAGE #10]
print("Tamper with the encrypted ticket blob so integrity check fails.")
bad_ticket = geordi_ticket[:-1] + ("A" if geordi_ticket[-1] != "A" else "B")
req = auth_req(RedeemRequest(event_id=event_id, ticket=bad_ticket),
               geor_priv, geor_pub, RedeemRequest).model_dump()
res = requests.post(SERVER_URL + "/redeem", json=req); tampered = parse_res(res)
show_req_res("Redeem with tampered ticket — expect FAIL", req, tampered)

# Proper flow: HOLDER redeem → OWNER stamp
print("Geordi redeems his transferred ticket to complete the holder-side path.")
req = auth_req(RedeemRequest(event_id=event_id, ticket=geordi_ticket),
               geor_priv, geor_pub, RedeemRequest).model_dump()
res = requests.post(SERVER_URL + "/redeem", json=req); r_ok = parse_res(res)
show_req_res("Redeem (Geordi)", req, r_ok)

# Owner verifies BEFORE stamp (should not see stamped state)
print("Beverly verifies without stamping to confirm stamped state is False.")
req = auth_req(
    VerifyRequest(event_id=event_id, ticket=geordi_ticket, check_public_key=geor_pub, stamp=False),
    beverly_priv, beverly_pub, VerifyRequest
).model_dump()
res = requests.post(SERVER_URL + "/verify", json=req); v_before_stamp_owner = parse_res(res)
show_req_res("Owner Verify AFTER Stamp (no-stamp flag) — should not show stamped", req, v_before_stamp_owner)

print("Beverly stamps after redemption; this is the decisive step that prevents repeat use.")
req = auth_req(VerifyRequest(event_id=event_id, ticket=geordi_ticket, check_public_key=geor_pub, stamp=True),
               beverly_priv, beverly_pub, VerifyRequest).model_dump()
res = requests.post(SERVER_URL + "/verify", json=req); v_stamp = parse_res(res)
show_req_res("Owner Verify with STAMP (Beverly)", req, v_stamp)

# Non-owner attempts to STAMP — should fail  [COVERAGE #2]
print("A non-owner attempts to STAMP — should be rejected by permissions.")
req = auth_req(VerifyRequest(event_id=event_id, ticket=geordi_ticket, check_public_key=geor_pub, stamp=True),
               rand_priv, rand_pub, VerifyRequest).model_dump()
res = requests.post(SERVER_URL + "/verify", json=req); non_owner_stamp = parse_res(res)
show_req_res("Non-owner STAMP — expect FAIL", req, non_owner_stamp)

# Owner verifies AFTER stamp (should see stamped state)
print("Beverly verifies again without stamping to confirm stamped state is visible to the owner.")
req = auth_req(
    VerifyRequest(event_id=event_id, ticket=geordi_ticket, check_public_key=geor_pub, stamp=False),
    beverly_priv, beverly_pub, VerifyRequest
).model_dump()
res = requests.post(SERVER_URL + "/verify", json=req); v_after_stamp_owner = parse_res(res)
show_req_res("Owner Verify AFTER Stamp (no-stamp flag) — should show stamped", req, v_after_stamp_owner)

# Non-owner verify AFTER stamp (should NOT show stamped state)
print("A non-owner verifies after stamping to confirm stamp info is hidden from outsiders.")
req = auth_req(
    VerifyRequest(event_id=event_id, ticket=geordi_ticket, check_public_key=geor_pub, stamp=False),
    rand_priv, rand_pub, VerifyRequest
).model_dump()
res = requests.post(SERVER_URL + "/verify", json=req); v_after_stamp_non_owner = parse_res(res)
show_req_res("Non-owner Verify AFTER Stamp (no-stamp flag) — should NOT show stamped", req, v_after_stamp_non_owner)


#$$$$$

#
print(
    "Furious at Wesley, but unable to find him, Beverly decides she is going " \
    "to attend the recital after all in an attempt to calm herself down.  " \
    "She calls up Geordi to ask for her ticket back, and he signs and sends "
    "her a transfer validation block.  She submits the request... but " \
    "doesn't know that Geordi's ticket has already been redeemed and stamped."
)


#
print(
    "Beverly is now livid at the situation, forcing Geordi to leave the " \
    "event to go and comfort her.  And upon his return, Geordi attempts to " \
    "re-redeem his ticket to streamline getting back inside before the show " \
    "starts."
)


print(
    "Jean-Luc knows that Geordi was at the event, so even though he can't " \
    "re-redeem, he decides to just try and stamp Geordi's ticket for a "
    "second time so he is defintiely marked as admitted."
)


print(
    "Meanwhile, Wesley has finally realized that instead of trying to steal " \
    "other people's tickets and credentials, he can simply register himself."
)

# Beverly tries to cancel his ticket

# She tells Jean-Luc and he cancels it when he shows up at the event

# Wesley attempts to redeem and transfer

# Wesley dresses up in a disguise and asks Jean-Luc to stamp his ticket -- which fails



# Transfer AFTER stamp — should fail  [COVERAGE #5]
print("Attempt to transfer a stamped ticket — should be blocked.")
tblk_after = auth_req(Transfer(ticket=geordi_ticket, transfer_public_key=rand_pub),
                      geor_priv, geor_pub, Transfer)
treq_after = auth_req(TransferRequest(event_id=event_id, transfer=tblk_after),
                      rand_priv, rand_pub, TransferRequest).model_dump()
res = requests.post(SERVER_URL + "/transfer", json=treq_after); tr_after = parse_res(res)
show_req_res("Transfer AFTER stamp — expect FAIL", treq_after, tr_after)

# Idempotence checks: double redeem (fail), double stamp (no-op/confirm)
print("Geordi tries to redeem again to verify a duplicate attempt fails gracefully.")
req = auth_req(RedeemRequest(event_id=event_id, ticket=geordi_ticket),
               geor_priv, geor_pub, RedeemRequest).model_dump()
res = requests.post(SERVER_URL + "/redeem", json=req); rd2 = parse_res(res)
show_req_res("Redeem again — expect FAIL", req, rd2)

print("Beverly stamps again to confirm idempotence (no-op/confirm semantics).")
req = auth_req(VerifyRequest(event_id=event_id, ticket=geordi_ticket, check_public_key=geor_pub, stamp=True),
               beverly_priv, beverly_pub, VerifyRequest).model_dump()
res = requests.post(SERVER_URL + "/verify", json=req); st2 = parse_res(res)
show_req_res("Stamp again — expect no-op/confirm stamped", req, st2)


### Wesley makes this ticket
# Cancellation: fresh ticket → non-owner cancel fail → owner cancel success → post-cancel denials
print("Jean-Luc takes a fresh ticket to test cancellation flows.")
req = auth_req(RegisterRequest(event_id=event_id), jean_priv, jean_pub, RegisterRequest).model_dump()
res = requests.post(SERVER_URL + "/register", json=req); j2 = parse_res(res)
show_req_res("Register fresh ticket (Jean-Luc)", req, j2)
jl2_ticket = j2["data"]["content"]["ticket"]

print("A non-owner attempts to cancel to ensure the system rejects unauthorized cancellations.")
req = auth_req(CancelRequest(event_id=event_id, ticket=jl2_ticket, check_public_key=jean_pub),
               geor_priv, geor_pub, CancelRequest).model_dump()
res = requests.post(SERVER_URL + "/cancel", json=req); cfail = parse_res(res)
show_req_res("Cancel by NON-OWNER — expect FAIL", req, cfail)

print("Beverly cancels the unused ticket to verify owner authority and blocked state thereafter.")
req = auth_req(CancelRequest(event_id=event_id, ticket=jl2_ticket, check_public_key=jean_pub),
               beverly_priv, beverly_pub, CancelRequest).model_dump()
res = requests.post(SERVER_URL + "/cancel", json=req); csucc = parse_res(res)
show_req_res("Cancel by OWNER (pre-redeem) — expect SUCCESS", req, csucc)

print("Post-cancel checks: redeem/transfer/stamp should all be rejected.")
req = auth_req(RedeemRequest(event_id=event_id, ticket=jl2_ticket),
               jean_priv, jean_pub, RedeemRequest).model_dump()
res = requests.post(SERVER_URL + "/redeem", json=req); pcr = parse_res(res)
show_req_res("Redeem canceled ticket — FAIL", req, pcr)

t_after_cancel = auth_req(Transfer(ticket=jl2_ticket, transfer_public_key=geor_pub),
                          jean_priv, jean_pub, Transfer)
treq_cancel = auth_req(TransferRequest(event_id=event_id, transfer=t_after_cancel),
                       geor_priv, geor_pub, TransferRequest).model_dump()
res = requests.post(SERVER_URL + "/transfer", json=treq_cancel); pct = parse_res(res)
show_req_res("Transfer canceled ticket — FAIL", treq_cancel, pct)

req = auth_req(VerifyRequest(event_id=event_id, ticket=jl2_ticket, check_public_key=jean_pub, stamp=True),
               beverly_priv, beverly_pub, VerifyRequest).model_dump()
res = requests.post(SERVER_URL + "/verify", json=req); pcs = parse_res(res)
show_req_res("Stamp canceled ticket — FAIL", req, pcs)

# This next pair remains as-is to exercise your current behavior; consider failing instead in prod.
req = auth_req(CancelRequest(event_id=event_id, ticket=geordi_ticket, check_public_key=geor_pub),
               beverly_priv, beverly_pub, CancelRequest).model_dump()
res = requests.post(SERVER_URL + "/cancel", json=req); csucc = parse_res(res)
show_req_res("Cancel Geordi's ticket — expect SUCCESS", req, csucc)

req = auth_req(VerifyRequest(event_id=event_id, ticket=geordi_ticket, check_public_key=geor_pub),
               beverly_priv, beverly_pub, VerifyRequest).model_dump()
res = requests.post(SERVER_URL + "/verify", json=req); pcs = parse_res(res)
show_req_res("Stamp canceled ticket — FAIL", req, pcs)

input("\n> Continue… ")

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