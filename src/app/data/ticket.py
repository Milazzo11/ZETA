"""
Ticket data models.

:author: Max Milazzo
"""



from .event import Event, EventSecrets
from .storage import ticket as ticket_storage
from app.crypto import hash
from app.crypto.symmetric import SKC
from app.error.errors import DomainException, ErrorKind

import base64
import json
from pydantic import BaseModel
from typing import Optional, Self



class Ticket(BaseModel):
    """
    User ticket data model.
    """

    event_id: str
    public_key: str
    number: int
    version: int
    metadata: Optional[str]
    event_secrets: EventSecrets


    @classmethod
    def register(
        cls,
        event_id: str,
        public_key: str,
        metadata: Optional[str] = None
    ) -> Self:
        """
        """

        number = Event.issue(event_id)
        event_secrets = EventSecrets.load(event_id)

        return cls(
            event_id=event_id,
            public_key=public_key,
            number=number,
            version=0,
            metadata=metadata,
            event_secrets=event_secrets
        )


    @classmethod
    def reissue(
        cls,
        event_id: str,
        public_key: str,
        number: int,
        version: int,
        metadata: Optional[str] = None
    ) -> Self:
        """
        """

        event_secrets = EventSecrets.load(event_id)
        
        if not ticket_storage.reissue(event_id, number, version):
            raise DomainException(ErrorKind.CONFLICT, "ticket transfer not allowed")
            # e.g., already redeemed or transfer limit reached

        return cls(
            event_id=event_id,
            public_key=public_key,
            number=number,
            version=version + 1,
            metadata=metadata,
            event_secrets=event_secrets
        )


    @classmethod
    def load(cls, event_id: str, public_key: str, ticket: str) -> Self:
        """
        """

        try:
            event_secrets = EventSecrets.load(event_id)

            b64_iv, ticket = ticket.split("-")
            cipher = SKC(key=event_secrets.event_key, iv=base64.b64decode(b64_iv))
        
            decrypted_ticket_raw = cipher.decrypt(ticket)
            decrypted_ticket = json.loads(decrypted_ticket_raw)
            ticket_data = decrypted_ticket["ticket"]
            ticket_string_raw = json.dumps(ticket_data)
            
            if hash.generate(ticket_string_raw) != decrypted_ticket["hash"]:
                raise DomainException(ErrorKind.PERMISSION, "ticket verification failed")
        
        except Exception:
            raise DomainException(ErrorKind.PERMISSION, "ticket verification failed")
            ## NOTE: do NOT use from e, this should be vague for security reasons

        if ticket_data["event_id"] != event_id:
            raise DomainException(ErrorKind.VALIDATION, "ticket for different event")
            # ensure ticket event ID matches the event ID passed by client

        if ticket_data["public_key"] != public_key:
            raise DomainException(ErrorKind.VALIDATION, "ticket for different user")
            # ensure ticket public key matches key of client making request

        if not ticket_storage.transfer_valid_check(event_id, ticket_data["number"], ticket_data["version"]):
            raise DomainException(ErrorKind.CONFLICT, "ticket superseded")
        
        return cls(
            event_id=event_id,
            public_key=public_key,
            number=ticket_data["number"],
            version=ticket_data["version"],
            metadata=ticket_data["metadata"],
            event_secrets=event_secrets
        )


        
    def redeem(self) -> None:
        """
        """

        if not ticket_storage.redeem(self.event_id, self.number, self.version):
            raise DomainException(ErrorKind.CONFLICT, "ticket already redeemed")
        

    def verify(self):
        return ticket_storage.verify(self.event_id, self.number)


    def pack(self) -> str:
        """
        Convert ticket data to encrypted string.
        """

        ticket_data = {
            "event_id": self.event_id,
            "public_key": self.public_key,
            "number": self.number,
            "version": self.version,
            "metadata": self.metadata
        }

        ticket_string_raw = json.dumps(ticket_data)
        ticket_string_hash = hash.generate(ticket_string_raw)

        verif_data = {
            "ticket": ticket_data,
            "hash": ticket_string_hash
        }
        verif_data_str = json.dumps(verif_data)

        cipher = SKC(key=self.event_secrets.event_key)
        encrypted_string = cipher.encrypt(verif_data_str)
        ticket_string = cipher.iv_b64() + "-" + encrypted_string

        return ticket_string