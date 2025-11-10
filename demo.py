"""
Simple demo/testing module.
"""


from app.API.models import *
from app.data.event import Event
from app.crypto.asymmetric import AKC
from app.util import keys, display

from src.app.data.storage.connection import pool
pool.close()

import time
import uuid
import copy
import requests


# --------------------------- CONFIG ---------------------------
SERVER_URL = "http://localhost:8000"
TIMESTAMP_ERROR = 10


# ---------------------- AUTH / VERIFY HELPERS -----------------
def auth_req(content, private_key, public_key, request_type):
    """
    Wraps a request model into Data[T], signs it, and returns Auth[T].
    """
    packet = Data[request_type].load(content)
    cipher = AKC(private_key=private_key)
    return Auth[request_type](
        data=packet,
        public_key=public_key,
        signature=cipher.sign(packet.model_dump())
    )


def auth_res(res_json) -> bool:
    """
    Verifies server response signature and timestamp freshness.
    """
    now = time.time()
    if abs(now - res_json["data"]["timestamp"]) > TIMESTAMP_ERROR:
        return False
    cipher = AKC(public_key=keys.pub())
    return cipher.verify(res_json["signature"], res_json["data"])


# ---------------------- CONDENSED LOGGING ---------------------
_LAST_STATUS = None  # capture last HTTP status so we can print it first

def narr(line: str) -> None:
    """One-liner narrative before each action."""
    print(f"\n• {line}")


def parse_res(res) -> dict:
    """
    Return JSON only; printing happens in show_req_res so we can print STATUS first.
    """
    global _LAST_STATUS
    _LAST_STATUS = res.status_code
    return res.json()


def show_req_res(title: str, req: dict, res_json: dict) -> None:
    """
    Compact request/response logging with STATUS first and an auth verdict.
    """
    print(f"\n== {title} ==")
    print(f"STATUS: {_LAST_STATUS}")
    print("\nREQUEST:", req)
    print("\nRESPONSE:", res_json)
    print("RESPONSE AUTH:", auth_res(res_json))
    print()

    input("> ")


# ----------------------------- MAIN ---------------------------
print("ZETA Demo (Condensed Story Mode)")
input("> Press Enter to begin… ")

# Crew keypairs
bev = AKC(); beverly_priv, beverly_pub = bev.private_key, bev.public_key
jl  = AKC();  jean_priv,  jean_pub    = jl.private_key,  jl.public_key
geo = AKC();  geor_priv,  geor_pub    = geo.private_key, geo.public_key
rnd = AKC();  rand_priv,  rand_pub    = rnd.private_key, rnd.public_key  # non-owner observer

# =========================== ACT I ============================
display.clear()
print("ACT I — Open gathering (unrestricted) with transfers, verifies, stamping, and cancellation.")

# Create event (unrestricted)
tea_evt = Event(name="Tea Party", description="Tea, Earl Grey, hot.", tickets=3, restricted=False)
narr("Beverly creates a small, orderly meetup to sanity-check the system before inviting chaos.")
req = auth_req(CreateRequest(event=tea_evt), beverly_priv, beverly_pub, CreateRequest).model_dump()
res = requests.post(SERVER_URL + "/create", json=req); rj = parse_res(res)
show_req_res("Create Event (Beverly)", req, rj)
tea_event_id = rj["data"]["content"]["event_id"]

# Search by text; Jean-Luc registers (success)
narr("Jean-Luc searches for the event; he prefers to go through the same flow as everyone else.")
req = auth_req(SearchRequest(text="tea", mode="text"), jean_priv, jean_pub, SearchRequest).model_dump()
res = requests.post(SERVER_URL + "/search", json=req); sr = parse_res(res)
show_req_res("Search 'tea' (Jean-Luc)", req, sr)

narr("Jean-Luc registers first — leading by example is his thing.")
req = auth_req(RegisterRequest(event_id=tea_event_id), jean_priv, jean_pub, RegisterRequest).model_dump()
res = requests.post(SERVER_URL + "/register", json=req); rj_reg = parse_res(res)
show_req_res("Register Event (Jean-Luc)", req, rj_reg)
jl_ticket = rj_reg["data"]["content"]["ticket"]

# Spoofed TRANSFER signature (should fail)
narr("An attacker forges the transfer signature; the holder identity must be enforced.")
# Build a correctly-shaped block (for structure)
_valid_transfer_shape = auth_req(
    Transfer(ticket=jl_ticket, transfer_public_key=geor_pub),
    jean_priv, jean_pub, Transfer
)

# Make a mismatched signature using the wrong private key
_wrong_sig_block = auth_req(
    Transfer(ticket=jl_ticket, transfer_public_key=geor_pub),
    rand_priv, rand_pub, Transfer
)

# Copy the valid shape but replace the signature with the wrong one
spoof_transfer = _valid_transfer_shape.model_dump()
spoof_transfer["signature"] = _wrong_sig_block.signature  # public_key remains Jean-Luc's

treq_spoof = auth_req(
    TransferRequest(event_id=tea_event_id, transfer=spoof_transfer),
    geor_priv, geor_pub, TransferRequest
).model_dump()

res = requests.post(SERVER_URL + "/transfer", json=treq_spoof)
tr_spoof = parse_res(res)
show_req_res("Transfer with SPOOFED signature — expect FAIL", treq_spoof, tr_spoof)

# Transfer: Jean-Luc → Geordi
narr("Jean-Luc transfers his spot to Geordi so the engineer can exercise the transfer pipeline end-to-end.")
tblk = auth_req(Transfer(ticket=jl_ticket, transfer_public_key=geor_pub), jean_priv, jean_pub, Transfer)
print("TRANSFER VALIDATION BLOCK: signed by current holder authorizing a new holder (omitted details).")
treq = auth_req(TransferRequest(event_id=tea_event_id, transfer=tblk), geor_priv, geor_pub, TransferRequest).model_dump()
res = requests.post(SERVER_URL + "/transfer", json=treq); tr = parse_res(res)
show_req_res("Transfer Ticket (Jean-Luc → Geordi)", treq, tr)
geordi_ticket = tr["data"]["content"]["ticket"]

# Jean-Luc tries to redeem old (transferred) ticket — should fail
narr("Jean-Luc tries redeeming his old ticket to confirm the system rejects post-transfer use.")
req = auth_req(RedeemRequest(event_id=tea_event_id, ticket=jl_ticket), jean_priv, jean_pub, RedeemRequest).model_dump()
res = requests.post(SERVER_URL + "/redeem", json=req); rr = parse_res(res)
show_req_res("Redeem Old Transferred Ticket — expect FAIL", req, rr)

# Double-transfer attempt — should fail
narr("Jean-Luc tries transferring the same ticket again to see that double-transfer is blocked.")
tblk2 = auth_req(Transfer(ticket=jl_ticket, transfer_public_key=geor_pub), jean_priv, jean_pub, Transfer)
treq2 = auth_req(TransferRequest(event_id=tea_event_id, transfer=tblk2), geor_priv, geor_pub, TransferRequest).model_dump()
res = requests.post(SERVER_URL + "/transfer", json=treq2); tr2 = parse_res(res)
show_req_res("Transfer Again Same Ticket — expect FAIL", treq2, tr2)

# (Testing-only) Owner verify BEFORE redemption — not needed in real flow
narr("Beverly performs a pre-redeem verify for testing; in practice stamping later is enough to prevent reuse.")
req = auth_req(VerifyRequest(event_id=tea_event_id, ticket=geordi_ticket, check_public_key=geor_pub),
               beverly_priv, beverly_pub, VerifyRequest).model_dump()
res = requests.post(SERVER_URL + "/verify", json=req); v_before = parse_res(res)
show_req_res("Owner Verify BEFORE Redeem (optional)", req, v_before)

# Non-owner verify (read-only)
narr("A non-owner does a verify-only check to confirm the ticket’s current state without any stamp authority.")
req = auth_req(VerifyRequest(event_id=tea_event_id, ticket=geordi_ticket, check_public_key=geor_pub),
               rand_priv, rand_pub, VerifyRequest).model_dump()
res = requests.post(SERVER_URL + "/verify", json=req); v_non_owner = parse_res(res)
show_req_res("Verify by NON-OWNER (read-only; no stamp)", req, v_non_owner)

# Owner attempts to redeem on behalf of holder — should fail
narr("Beverly attempts to redeem on Geordi’s behalf; the system should require the holder’s signature.")
req = auth_req(RedeemRequest(event_id=tea_event_id, ticket=geordi_ticket),
               beverly_priv, beverly_pub, RedeemRequest).model_dump()
res = requests.post(SERVER_URL + "/redeem", json=req); orf = parse_res(res)
show_req_res("Owner tries to redeem FOR holder — expect FAIL", req, orf)

# Proper flow: HOLDER redeem → OWNER stamp
narr("Geordi redeems his transferred ticket to complete the holder-side path.")
req = auth_req(RedeemRequest(event_id=tea_event_id, ticket=geordi_ticket),
               geor_priv, geor_pub, RedeemRequest).model_dump()
res = requests.post(SERVER_URL + "/redeem", json=req); r_ok = parse_res(res)
show_req_res("Redeem (Geordi)", req, r_ok)

# Owner verifies BEFORE stamp (should not see stamped state)
narr("Beverly verifies without stamping to confirm stamped state is False.")
req = auth_req(
    VerifyRequest(event_id=tea_event_id, ticket=geordi_ticket, check_public_key=geor_pub, stamp=False),
    beverly_priv, beverly_pub, VerifyRequest
).model_dump()
res = requests.post(SERVER_URL + "/verify", json=req); v_before_stamp_owner = parse_res(res)
show_req_res("Owner Verify AFTER Stamp (no-stamp flag) — should not show stamped", req, v_before_stamp_owner)

narr("Beverly stamps after redemption; this is the decisive step that prevents repeat use.")
req = auth_req(VerifyRequest(event_id=tea_event_id, ticket=geordi_ticket, check_public_key=geor_pub, stamp=True),
               beverly_priv, beverly_pub, VerifyRequest).model_dump()
res = requests.post(SERVER_URL + "/verify", json=req); v_stamp = parse_res(res)
show_req_res("Owner Verify with STAMP (Beverly)", req, v_stamp)

# Owner verifies AFTER stamp (should see stamped state)
narr("Beverly verifies again without stamping to confirm stamped state is visible to the owner.")
req = auth_req(
    VerifyRequest(event_id=tea_event_id, ticket=geordi_ticket, check_public_key=geor_pub, stamp=False),
    beverly_priv, beverly_pub, VerifyRequest
).model_dump()
res = requests.post(SERVER_URL + "/verify", json=req); v_after_stamp_owner = parse_res(res)
show_req_res("Owner Verify AFTER Stamp (no-stamp flag) — should show stamped", req, v_after_stamp_owner)

# Non-owner verify AFTER stamp (should NOT show stamped state)
narr("A non-owner verifies after stamping to confirm stamp info is hidden from outsiders.")
req = auth_req(
    VerifyRequest(event_id=tea_event_id, ticket=geordi_ticket, check_public_key=geor_pub, stamp=False),
    rand_priv, rand_pub, VerifyRequest
).model_dump()
res = requests.post(SERVER_URL + "/verify", json=req); v_after_stamp_non_owner = parse_res(res)
show_req_res("Non-owner Verify AFTER Stamp (no-stamp flag) — should NOT show stamped", req, v_after_stamp_non_owner)

# Idempotence checks: double redeem (fail), double stamp (no-op/confirm)
narr("Geordi tries to redeem again to verify a duplicate attempt fails gracefully.")
req = auth_req(RedeemRequest(event_id=tea_event_id, ticket=geordi_ticket),
               geor_priv, geor_pub, RedeemRequest).model_dump()
res = requests.post(SERVER_URL + "/redeem", json=req); rd2 = parse_res(res)
show_req_res("Redeem again — expect FAIL", req, rd2)

narr("Beverly stamps again to confirm idempotence (no-op/confirm semantics).")
req = auth_req(VerifyRequest(event_id=tea_event_id, ticket=geordi_ticket, check_public_key=geor_pub, stamp=True),
               beverly_priv, beverly_pub, VerifyRequest).model_dump()
res = requests.post(SERVER_URL + "/verify", json=req); st2 = parse_res(res)
show_req_res("Stamp again — expect no-op/confirm stamped", req, st2)

# Cancellation: fresh ticket → non-owner cancel fail → owner cancel success → post-cancel denials
narr("Jean-Luc takes a fresh ticket to test cancellation flows.")
req = auth_req(RegisterRequest(event_id=tea_event_id), jean_priv, jean_pub, RegisterRequest).model_dump()
res = requests.post(SERVER_URL + "/register", json=req); j2 = parse_res(res)
show_req_res("Register fresh ticket (Jean-Luc)", req, j2)
jl2_ticket = j2["data"]["content"]["ticket"]

narr("A non-owner attempts to cancel to ensure the system rejects unauthorized cancellations.")
req = auth_req(CancelRequest(event_id=tea_event_id, ticket=jl2_ticket, check_public_key=jean_pub),
               geor_priv, geor_pub, CancelRequest).model_dump()
res = requests.post(SERVER_URL + "/cancel", json=req); cfail = parse_res(res)
show_req_res("Cancel by NON-OWNER — expect FAIL", req, cfail)

narr("Beverly cancels the unused ticket to verify owner authority and blocked state thereafter.")
req = auth_req(CancelRequest(event_id=tea_event_id, ticket=jl2_ticket, check_public_key=jean_pub),
               beverly_priv, beverly_pub, CancelRequest).model_dump()
res = requests.post(SERVER_URL + "/cancel", json=req); csucc = parse_res(res)
show_req_res("Cancel by OWNER (pre-redeem) — expect SUCCESS", req, csucc)

narr("Post-cancel checks: redeem/transfer/stamp should all be rejected.")
req = auth_req(RedeemRequest(event_id=tea_event_id, ticket=jl2_ticket),
               jean_priv, jean_pub, RedeemRequest).model_dump()
res = requests.post(SERVER_URL + "/redeem", json=req); pcr = parse_res(res)
show_req_res("Redeem canceled ticket — FAIL", req, pcr)

t_after_cancel = auth_req(Transfer(ticket=jl2_ticket, transfer_public_key=geor_pub),
                          jean_priv, jean_pub, Transfer)
treq_cancel = auth_req(TransferRequest(event_id=tea_event_id, transfer=t_after_cancel),
                       geor_priv, geor_pub, TransferRequest).model_dump()
res = requests.post(SERVER_URL + "/transfer", json=treq_cancel); pct = parse_res(res)
show_req_res("Transfer canceled ticket — FAIL", treq_cancel, pct)

req = auth_req(VerifyRequest(event_id=tea_event_id, ticket=jl2_ticket, check_public_key=jean_pub, stamp=True),
               beverly_priv, beverly_pub, VerifyRequest).model_dump()
res = requests.post(SERVER_URL + "/verify", json=req); pcs = parse_res(res)
show_req_res("Stamp canceled ticket — FAIL", req, pcs)

req = auth_req(CancelRequest(event_id=tea_event_id, ticket=geordi_ticket, check_public_key=geor_pub),
               beverly_priv, beverly_pub, CancelRequest).model_dump()
res = requests.post(SERVER_URL + "/cancel", json=req); csucc = parse_res(res)
show_req_res("Cancel Geordi's ticket — expect SUCCESS", req, csucc)

req = auth_req(VerifyRequest(event_id=tea_event_id, ticket=geordi_ticket, check_public_key=geor_pub),
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
narr("Deanna creates a restricted session; she admits people selectively.")
req = auth_req(CreateRequest(event=evt), deanna_priv, deanna_pub, CreateRequest).model_dump()
res = requests.post(SERVER_URL + "/create", json=req); rcreate = parse_res(res)
show_req_res("Create Restricted Event (Deanna)", req, rcreate)
counsel_id = rcreate["data"]["content"]["event_id"]

# Replay same signed create — should fail (nonce replay)
narr("Exact replay of the signed create to confirm nonce replay protection.")
res = requests.post(SERVER_URL + "/create", json=req); replay = parse_res(res)
show_req_res("Replay same signed /create — FAIL", req, replay)

# Expired timestamp
narr("Expired timestamp attempt to verify freshness enforcement.")
req_stale = copy.deepcopy(req); req_stale["data"]["timestamp"] -= (TIMESTAMP_ERROR + 1)
res = requests.post(SERVER_URL + "/create", json=req_stale); stale = parse_res(res)
show_req_res("Expired timestamp /create — FAIL", req_stale, stale)

# Tamper after signature
narr("Tampered payload (nonce changed after signing) to confirm signature binding.")
req_tamper = copy.deepcopy(req); req_tamper["data"]["nonce"] = str(uuid.uuid4()); req_tamper["data"]["timestamp"] = time.time()
res = requests.post(SERVER_URL + "/create", json=req_tamper); tamp = parse_res(res)
show_req_res("Tampered /create — FAIL", req_tamper, tamp)

# William tries to register without verification — fail
narr("William tries to register without a verification block to confirm restriction is enforced.")
req = auth_req(RegisterRequest(event_id=counsel_id), will_priv, will_pub, RegisterRequest).model_dump()
res = requests.post(SERVER_URL + "/register", json=req); w_fail = parse_res(res)
show_req_res("Restricted register WITHOUT verification — FAIL (William)", req, w_fail)

# Deanna creates a verification block for William; display note
narr("Deanna issues a verification block for William because she trusts his judgment.")
v_will = auth_req(Verification(event_id=counsel_id, public_key=will_pub, metadata="approved"),
                  deanna_priv, deanna_pub, Verification)
print("REGISTRATION VERIFICATION BLOCK: signed by owner, authorizing registrant (omitted details).")

# William registers with verification — success
narr("William registers with the owner’s verification, proving the allow-list works.")
req = auth_req(RegisterRequest(event_id=counsel_id, verification=v_will),
               will_priv, will_pub, RegisterRequest).model_dump()
res = requests.post(SERVER_URL + "/register", json=req); w_ok = parse_res(res)
show_req_res("Restricted register WITH verification — SUCCESS (William)", req, w_ok)
will_ticket = w_ok["data"]["content"]["ticket"]

# Spoofed VERIFICATION signature (should fail)
narr("An attacker spoofs the owner's signature on a verification block; registration must be rejected.")

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
narr("Reginald attempts to reuse a block tied to William’s key to confirm key-binding is honored.")
v_wrong = auth_req(Verification(event_id=counsel_id, public_key=will_pub, metadata="wrong-key"),
                   deanna_priv, deanna_pub, Verification)
req = auth_req(RegisterRequest(event_id=counsel_id, verification=v_wrong),
               reg_priv, reg_pub, RegisterRequest).model_dump()
res = requests.post(SERVER_URL + "/register", json=req); rw = parse_res(res)
show_req_res("Restricted register with WRONG-key verification — FAIL (Reginald)", req, rw)

# Correct verification for Reginald — success
narr("Deanna issues a new verification block for Reginald that matches his key.")
v_reg = auth_req(Verification(event_id=counsel_id, public_key=reg_pub),
                 deanna_priv, deanna_pub, Verification)
print("REGISTRATION VERIFICATION BLOCK: valid for Reginald (omitted details).")
req = auth_req(RegisterRequest(event_id=counsel_id, verification=v_reg),
               reg_priv, reg_pub, RegisterRequest).model_dump()
res = requests.post(SERVER_URL + "/register", json=req); r_ok = parse_res(res)
show_req_res("Restricted register WITH verification — SUCCESS (Reginald)", req, r_ok)
reg_ticket = r_ok["data"]["content"]["ticket"]

# Sold-out: Wesley has valid verification but event is full — should fail
narr("Wesley arrives late with a valid verification, but capacity is already reached.")
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
    narr(f"Owner verifies {who} without stamping (optional pre-check).")
    req = auth_req(VerifyRequest(event_id=counsel_id, ticket=ticket, check_public_key=w_pub),
                   deanna_priv, deanna_pub, VerifyRequest).model_dump()
    res = requests.post(SERVER_URL + "/verify", json=req); pv = parse_res(res)
    show_req_res(f"Owner Verify (no stamp) — {who}", req, pv)

    narr(f"{who} redeems their ticket; holder’s signature proves possession.")
    req = auth_req(RedeemRequest(event_id=counsel_id, ticket=ticket),
                   w_priv, w_pub, RedeemRequest).model_dump()
    res = requests.post(SERVER_URL + "/redeem", json=req); red = parse_res(res)
    show_req_res(f"Redeem — {who}", req, red)

    narr(f"Owner stamps {who}'s ticket after redemption; this prevents repeat use.")
    req = auth_req(VerifyRequest(event_id=counsel_id, ticket=ticket, check_public_key=w_pub, stamp=True),
                   deanna_priv, deanna_pub, VerifyRequest).model_dump()
    res = requests.post(SERVER_URL + "/verify", json=req); st = parse_res(res)
    show_req_res(f"Owner STAMP — {who}", req, st)

    # Owner re-verify sees stamp
    narr(f"Owner re-verifies {who}'s ticket without stamping, confirming stamped state is recorded.")
    req = auth_req(
        VerifyRequest(event_id=counsel_id, ticket=ticket, check_public_key=w_pub, stamp=False),
        deanna_priv, deanna_pub, VerifyRequest
    ).model_dump()
    res = requests.post(SERVER_URL + "/verify", json=req); vs_owner = parse_res(res)
    show_req_res(f"Owner Verify AFTER Stamp (no-stamp flag) — {who}", req, vs_owner)

    # Non-owner re-verify does NOT see stamp
    narr(f"A non-owner verifies {who}'s ticket and should NOT see stamped state.")
    req = auth_req(
        VerifyRequest(event_id=counsel_id, ticket=ticket, check_public_key=w_pub, stamp=False),
        rand_priv, rand_pub, VerifyRequest
    ).model_dump()
    res = requests.post(SERVER_URL + "/verify", json=req); vs_non_owner = parse_res(res)
    show_req_res(f"Non-owner Verify AFTER Stamp (no-stamp flag) — {who}", req, vs_non_owner)

# Deletion behavior
narr("Deanna checks that the event exists by ID, then deletes it, then confirms it’s gone.")
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