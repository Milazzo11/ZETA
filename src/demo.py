from client import EventAPI
import time


###TODO -- this needs to actually be built well


def main():
    api_client = EventAPI(
        private_key_path="priv.demo.key",
        public_key_path="pub.demo.key",
        base_url="http://localhost:8000",
    )

    print("BITicket demo!")
    print("(note: the same public key is used for all requests, as this is only a demonstration)")
    print("Enjoy!")
    input("> ")

    print("\nKathryn creates a new event: \"Coming Home Party\"")
    res = api_client.create_event(
        event_id="",
        event_name="Coming Home Party",
        event_description="No place like home",
        tickets=1000,
        start=time.time(),
        end=time.time() * 2,
        private=False,
    )
    print(res.status_code, res.json())
    print("VALID SIGNATURE:", api_client.check_signature(res.json()))
    input("> ")

    print("\nReginald wants to be a part of this event, so he searches \"Coming Home\" to find the event ID")
    res = api_client.search_event("Coming Home", 1, "text")
    event_id = res.json()["data"]["content"]["events"][0]["id"]
    print(res.status_code, res.json())
    print("VALID SIGNATURE:", api_client.check_signature(res.json()))
    input("> ")

    print("\nHe then registers and receieves a ticket")
    res = api_client.register_user(event_id)
    reg_ticket = res.json()["data"]["content"]["ticket"]
    print(res.status_code, res.json())
    print("VALID SIGNATURE:", api_client.check_signature(res.json()))
    input("> ")


    print("\nAfter 7 years of waiting and anticipation... The \"Coming Home Party\" finally arrives!")
    print("Reg meets his old friend Katie at the door, and redeems his ticket")
    res = api_client.redeem_ticket(event_id, reg_ticket)
    print(res.status_code, res.json())
    print("VALID SIGNATURE:", api_client.check_signature(res.json()))
    input("> ")

    print("\nKathryn and Reg might be good friends... but she still wants to make sure he's really registered for the event and redeemed his ticket")
    print("For all she knows, \"Reg\" could actually be a shapeshifter trying to infiltrate her party!")
    print("So, Reg shows her his public key, as well as a signature generated using his associated private key (proving he owns that key)")
    input("> ")

    print("\nThen, Katie verifies the redemption with the server")
    res = api_client.verify(event_id, reg_ticket, api_client.public_key)
    print(res.status_code, res.json())
    print("VALID SIGNATURE:", api_client.check_signature(res.json()))
    input("> ")

    print("\nBut Reg realizes that he forgot to get a ticket for his cat Neelix!  So he quickly registers another ticket for him")
    res = api_client.register_user(event_id)
    neelix_ticket = res.json()["data"]["content"]["ticket"]
    print(res.status_code, res.json())
    print("VALID SIGNATURE:", api_client.check_signature(res.json()))
    input("> ")

    print("\nReg runs back to the party and asks Kathryn to verify his cat's redemption...")
    res = api_client.verify(event_id, neelix_ticket, api_client.public_key)
    print(res.status_code, res.json())
    print("VALID SIGNATURE:", api_client.check_signature(res.json()))
    input("> ")

    print("\nBut in his haste, Reg forgot to redeem the ticket for his poor kitty!")
    print("Luckily, Kathryn doesn't seem to care much, and she lets them both through!")
    input("> ")

    print("\nNot everyone wants to follow the rules, though...")
    print("Kathryn's old nemsis Seska is throwing her own party")
    print("She creates her own event: \"Evil People Convention\"")
    res = api_client.create_event(
        event_id="",
        event_name="Evil People Convention",
        event_description="I hate everyone (except maybe Chakotay)",
        tickets=1001,
        start=time.time(),
        end=time.time() * 2,
        private=False,
    )
    seska_event_id = res.json()["data"]["content"]["event_id"]
    print(res.status_code, res.json())
    print("VALID SIGNATURE:", api_client.check_signature(res.json()))
    input("> ")

    print("\nThen Seska registers for her own event and recieves a ticket")
    res = api_client.register_user(seska_event_id)
    seska_ticket = res.json()["data"]["content"]["ticket"]
    print(res.status_code, res.json())
    print("VALID SIGNATURE:", api_client.check_signature(res.json()))
    input("> ")

    print("\nSeska now has a brilliant plan... she'll just use this ticket to crash Kathryn's event!'")
    print("So she redeems her ticket (for her own event).")
    res = api_client.redeem_ticket(seska_event_id, seska_ticket)
    print(res.status_code, res.json())
    print("VALID SIGNATURE:", api_client.check_signature(res.json()))
    input("> ")

    print("\nSeska walks up to the door to the party and waits while Katie sends the verification request...")
    res = api_client.verify(event_id, seska_ticket, api_client.public_key)
    print(res.status_code, res.json())
    print("VALID SIGNATURE:", api_client.check_signature(res.json()))
    input("> ")

    print("\n... but unfortunately for Seska, her plan is easily foiled, and she is thrown out!")
    print("The end.")
    input("> ")


if __name__ == "__main__":
    main()