"""
Ticket data model.

:author: Max Milazzo
"""



from .event import Event
from app.data.storage import ticket_store
from app.crypto import hash
from app.crypto.symmetric import SKC
from app.error.errors import DomainException, ErrorKind

import base64
import json
from pydantic import BaseModel
from typing import Optional, Self



REDEEMED_BYTE = 1 << 6
# redeemed byte value: 0b01000000


STAMPED_BYTE = 1 << 7
# stamped byte value is: 0b10000000


CANCELED_BYTE = (1 << 7) | (1 << 6)
# canceled byte value: 0b11000000



class Ticket(BaseModel):
    """
    User ticket data model.
    """

    event_id: str
    public_key: str
    number: int
    version: int
    metadata: Optional[str]
    event_key: bytes


    @staticmethod
    def _validate(event_id: str, number: int, version: int) -> None:
        """
        Validate that the requester's ticket.

        :param event_id: unique event identifier
        :param number: ticket issue number
        :param version: requester's ticket version
        """

        byte = ticket_store.load_state_byte(event_id, number)

        if byte is None:
            raise DomainException(ErrorKind.NOT_FOUND, "event not found")
        
        if (byte & CANCELED_BYTE) == CANCELED_BYTE:
            raise DomainException(ErrorKind.CONFLICT, "ticket canceled")
            # check if the ticket has been canceled
            # (a ticket is canceled if the first 2 bits are on)

        if not ((byte & (REDEEMED_BYTE - 1)) == version):
            raise DomainException(ErrorKind.CONFLICT, "ticket superseded")
            # check if the ticket version is up to date
            # (a ticket version is valid if the low 6 bits match the expected version)


    @classmethod
    def register(
        cls,
        event_id: str,
        public_key: str,
        metadata: Optional[str] = None
    ) -> Self:
        """
        Register a new user for an event to receieve a ticket.

        :param event_id: unique event identifier
        :param public_key: requester's public key
        :param metadata: optional metadata to embded in ticket
        :return: ticket model
        """

        number = ticket_store.issue(event_id)

        if number is None:
            raise DomainException(ErrorKind.CONFLICT, "unable to issue ticket")

        return cls(
            event_id=event_id,
            public_key=public_key,
            number=number,
            version=0,
            metadata=metadata,
            event_key=Event.get_key(event_id)
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
        Reissue a ticket to complete a transfer from one user to another.

        :param event_id: unique event identifier
        :param public_key: public key of the requester (transfer recipient)
        :param number: ticket issue number
        :param version: current ticket version (pre-transfer)
        :param metadata: optional metadata to embded in ticket
        :return: ticket model
        """

        if version == REDEEMED_BYTE - 1:
            raise DomainException(ErrorKind.CONFLICT, "ticket transfer limit reached")
            # tickets with version 0b00111111 can no longer be transferred
            # (version data is maxed out)
        
        if not ticket_store.reissue(event_id, number, version):
            raise DomainException(ErrorKind.CONFLICT, "ticket transfer failed")

        return cls(
            event_id=event_id,
            public_key=public_key,
            number=number,
            version=version + 1,
            metadata=metadata,
            event_key=Event.get_key(event_id)
        )


    @classmethod
    def load(cls, event_id: str, public_key: str, ticket: str) -> Self:
        """
        Decrypt and load a requester's encrypted ticket string as a ticket data model.

        :param event_id: unique event identifier
        :param public_key: requester's public key
        :param ticket: requester's encrypted ticket string
        :return: ticket model
        """

        try:
            event_key = Event.get_key(event_id)

            b64_iv, ticket = ticket.split("-")
            cipher = SKC(key=event_key, iv=base64.b64decode(b64_iv))
        
            decrypted_ticket_raw = cipher.decrypt(ticket)
            decrypted_ticket = json.loads(decrypted_ticket_raw)
            ticket_data = decrypted_ticket["ticket"]
            ticket_string_raw = json.dumps(ticket_data)
            
            if hash.generate(ticket_string_raw) != decrypted_ticket["hash"]:
                raise DomainException(ErrorKind.PERMISSION, "ticket verification failed")
                # check that the decrypted ticket's stored hash value is correct
                # (error message purposefully kept vague for security)
        
        except DomainException:
            raise

        except Exception:
            raise DomainException(ErrorKind.PERMISSION, "ticket verification failed") 
            # handle general decryption failure
            # (error message purposefully kept vague for security)

        if ticket_data["public_key"] != public_key:
            raise DomainException(ErrorKind.VALIDATION, "ticket for different user")
            # ensure ticket public key matches key of client making request

        if ticket_data["event_id"] != event_id:
            raise DomainException(ErrorKind.VALIDATION, "ticket for different event")
            # ensure ticket event ID matches the event ID passed by client
            # (this error should not trigger unless the original server ticket issuance
            # response was tampered with or compromised)

        cls._validate(
            event_id,
            ticket_data["number"],
            ticket_data["version"]
        )
        
        return cls(
            event_id=event_id,
            public_key=public_key,
            number=ticket_data["number"],
            version=ticket_data["version"],
            metadata=ticket_data["metadata"],
            event_key=event_key
        )


    def redeem(self) -> None:
        """
        Redeem the current ticket.
        """

        if not ticket_store.advance_state(
            self.event_id,
            self.number,
            self.version | REDEEMED_BYTE,
            REDEEMED_BYTE
        ):
            raise DomainException(ErrorKind.CONFLICT, "ticket redemption failed")
        

    def cancel(self) -> None:
        """
        Cancel the current ticket.
        """

        if not ticket_store.advance_state(
            self.event_id,
            self.number,
            self.version | CANCELED_BYTE,
            CANCELED_BYTE
        ):
            raise DomainException(ErrorKind.CONFLICT, "ticket cancelation failed")
        

    def verify(self) -> tuple[bool, bool]:
        """
        Verify redemption and stamped status of the current ticket.

        :return: redemption status, stamped status
        """

        byte = ticket_store.load_state_byte(self.event_id, self.number)

        if byte is None:
            raise DomainException(ErrorKind.NOT_FOUND, "event not found")
        
        if byte >= CANCELED_BYTE:
            raise DomainException(ErrorKind.NOT_FOUND, "ticket canceled")
        
        return byte >= REDEEMED_BYTE, byte >= STAMPED_BYTE
    

    def stamp(self) -> tuple[bool, bool]:
        """
        Stamp the current ticket.

        :return: redemption status (True), stamped status (True)
        """

        redeemed, stamped = self.verify()

        if not redeemed:
            raise DomainException(ErrorKind.CONFLICT, "ticket has not been redeemed")
                
        if stamped:
            raise DomainException(ErrorKind.CONFLICT, "ticket is already stamped")

        if not ticket_store.advance_state(
            self.event_id,
            self.number,
            self.version | STAMPED_BYTE,
            STAMPED_BYTE
        ):
            raise DomainException(ErrorKind.CONFLICT, "ticket stamping failed")
        
        return True, True


    def pack(self) -> str:
        """
        Convert the current ticket model to an encrypted ticket string.

        :return: encrypted ticket string
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

        cipher = SKC(key=self.event_key)
        encrypted_string = cipher.encrypt(verif_data_str)
        ticket_string = cipher.iv_b64() + "-" + encrypted_string

        return ticket_string