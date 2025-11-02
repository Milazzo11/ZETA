
from pydantic import BaseModel, Field
from typing import Optional

from .storage import ticket as ticket_db
from .event import EventData


from app.crypto.symmetric import SKE

from fastapi import HTTPException

from app.crypto import hash
import base64

from config import RETURN_QUEUE_MAX


class Ticket(BaseModel):
    event_id: str
    public_key: str
    number: int
    event_data: EventData

    @classmethod
    def register(self, event_id, public_key, number: Optional[int] = None) -> "Ticket":###maybe return ticket object
        
        event_data = EventData.load(event_id)

        if number is None:
            number = event_data.next_ticket()

        else:
            ticket_db.cancel(event_id, number)
            # cancel current ticket version

        ticket_db.register(event_id, number)

        return self(
            event_id=event_id,
            public_key=public_key,
            number=number,
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
        
            print(decrypted_ticket_raw)
            print(decrypted_ticket_raw.split("#"))
            decrypted_ticket, ticket_hash = decrypted_ticket_raw.split("#")
            
            if hash.generate(decrypted_ticket) != ticket_hash:
                raise Exception
                # go to "except" block

            ticket_data = decrypted_ticket.split("\\")
            assert len(ticket_data) == 3
        
        except:
            raise HTTPException(status_code=401, detail="Ticket verification failed")
            ## TODO - this is here and general to prevent padding oracle attack

        if ticket_data[0] != event_id:
            raise HTTPException(status_code=400, detail="Ticket data does not match event ID")
            # ensure ticket event ID matches the event ID passed by client

        if ticket_data[1] != public_key:
            raise HTTPException(status_code=400, detail="Ticket invalid (non-matching public key)")
            # ensure ticket public key matches key of client making request

        number = int(ticket_data[2])
        
        return self(
            event_id=event_id,
            public_key=public_key,
            number=number,
            event_data=event_data
        )



    def cancel(self) -> None:
        """
        """

        data = self.event_data.data

        if len(data.returned) >= RETURN_QUEUE_MAX:
            raise HTTPException(401, detail="Return queue full")
        
        if not ticket_db.cancel(self.event_id, self.number):
            raise HTTPException(400, detail="Maximum ticket cancellations reached")

        ticket_db.reissue(self.event_id, self.number)

        
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

        ticket_string_raw = self.event_id + "\\" + self.public_key + "\\" + str(self.number)
        ticket_string_hash = hash.generate(ticket_string_raw)

        encrypted_string = cipher.encrypt(ticket_string_raw + "#" + ticket_string_hash)
        ticket_string = cipher.iv_b64() + "-" + encrypted_string

        return ticket_string
        ## TODO - in future versions (prob not proof of concept) add ticket cancelation number in ticket string






### thought -- ticket stuff seems logical to use OOP (since everything ticket related can just be handled in here)