
from pydantic import BaseModel, Field
from typing import Optional

from .storage import ticket as ticket_db
from .event import EventData


from app.crypto.symmetric import SKE

from fastapi import HTTPException

from app.crypto import hash
import base64

from config import RETURN_QUEUE_MAX
import json


class Ticket(BaseModel):
    event_id: str
    public_key: str
    number: int
    metadata: Optional[str]
    event_data: EventData

    ### TODO * PROBABLY split into register/reissue?
    @classmethod
    def register(
        self, event_id: str, public_key: str, number: Optional[int] = None,
        metadata: Optional[str] = None
    ) -> "Ticket":
        """
        """

        event_data = EventData.load(event_id)

        if number is None:
            number = event_data.next_ticket()
            ticket_db.register(event_id, number)
        
        else:
            ticket_db.reissue(event_id, number)
            ### TODO* reissue increments transfer number

        ###else:
        ###    ticket_db.cancel(event_id, number)
        ###    # cancel current ticket version

        return self(
            event_id=event_id,
            public_key=public_key,
            number=number,
            metadata=metadata,
            event_data=event_data
        )


    @classmethod
    def load(self, event_id: str, public_key: str, ticket: str) -> "Ticket":
        """
        """
        ### TODO - prob add better error handling for failures... especially since CBC doesnt do integrity

        try:
            event_data = EventData.load(event_id)

            b64_iv, ticket = ticket.split("-")
            data = event_data.data

            cipher = SKE(key=data.event_key, iv=base64.b64decode(b64_iv))
        
            decrypted_ticket_raw = cipher.decrypt(ticket)
            decrypted_ticket = json.loads(decrypted_ticket_raw)
            ticket_data = decrypted_ticket["ticket"]
            
            if hash.generate(decrypted_ticket) != decrypted_ticket["hash"]:
                raise Exception
                # go to "except" block
        
        except:
            raise HTTPException(status_code=401, detail="Ticket verification failed")
            ## TODO - this is here and general to prevent padding oracle attack

        if ticket_data["event_id"] != event_id:
            raise HTTPException(status_code=400, detail="Ticket data does not match event ID")
            # ensure ticket event ID matches the event ID passed by client

        if ticket_data["public_key"] != public_key:
            raise HTTPException(status_code=400, detail="Ticket invalid (non-matching public key)")
            # ensure ticket public key matches key of client making request
        
        return self(
            event_id=event_id,
            public_key=public_key,
            number=ticket_data["number"],
            metadata=ticket_data["metadata"],
            event_data=event_data
        )


        
    def redeem(self) -> None:
        """
        """

        if not ticket_db.redeem(self.event_id, self.number):
            raise HTTPException(400, detail="Ticket has already been redeemed")
        

    def verify(self):
        return ticket_db.verify(self.event_id, self.number)


    def pack(self) -> str:
        """
        Convert ticket data to encrypted string.
        """

        data = self.event_data.data
        cipher = SKE(key=data.event_key)

        ticket_data = {
            "event_id": self.event_id,
            "public_key": self.public_key,
            "number": self.number,
            "metadata": self.metadata
        }

        ticket_string_raw = json.dumps(ticket_data)
        ticket_string_hash = hash.generate(ticket_string_raw)

        verif_data = {
            "ticket": ticket_string_raw,
            "hash": ticket_string_hash
        }
        verif_data_str = json.dumps(verif_data)

        encrypted_string = cipher.encrypt(verif_data_str)
        ticket_string = cipher.iv_b64() + "-" + encrypted_string

        return ticket_string
        ## TODO - in future versions (prob not proof of concept) add ticket cancelation number in ticket string






### thought -- ticket stuff seems logical to use OOP (since everything ticket related can just be handled in here)