"""
Ticket data model.

:author: Max Milazzo
"""



from .event import Event
from .storage import ticket as ticket_storage
from app.crypto import hash
from app.crypto.symmetric import SKC
from app.error.errors import DomainException, ErrorKind

import base64
import json
from pydantic import BaseModel
from typing import Optional, Self



REDEEMED_BYTE = 2 ** (8 - 1)
# value added (or bitwise ORed) to ticket byte data to signal redemption
# (the high bit determines redemption status, and all other bits determine version,
# therefore, the redemption byte value is: 0b10000000)



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
    def _validate_version(event_id: str, number: int, version: int) -> bool:
        """
        Validate that the requester's ticket is the most recent version (untransferred).

        :param event_id: unique event identifier
        :param number: ticket issue number
        :param version: requester's ticket version
        :return: ticket version validity status
        """

        byte = ticket_storage.get_data_byte(event_id, number)

        if byte is None:
            return DomainException(ErrorKind.NOT_FOUND, "event not found")

        return (byte & (REDEEMED_BYTE - 1)) == version
        # a ticket version is valid if the low 7 bits match the expected version
        # (the high bit represents redemption and may be set or unset)


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

        number = ticket_storage.issue(event_id)

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
            # tickets with version 0b01111111 can no longer be transferred
            # (version data is maxed out)
        
        if not ticket_storage.reissue(event_id, number, version):
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
        
        except Exception:
            raise DomainException(ErrorKind.PERMISSION, "ticket verification failed")
            # handle general decryption failure
            # (error message purposefully kept vague for security)

        if ticket_data["event_id"] != event_id:
            raise DomainException(ErrorKind.VALIDATION, "ticket for different event")
            # ensure ticket event ID matches the event ID passed by client

        if ticket_data["public_key"] != public_key:
            raise DomainException(ErrorKind.VALIDATION, "ticket for different user")
            # ensure ticket public key matches key of client making request

        if not cls._validate_version(
            event_id,
            ticket_data["number"],
            ticket_data["version"]
        ):
            raise DomainException(ErrorKind.CONFLICT, "ticket superseded")
        
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

        if not ticket_storage.redeem(
            self.event_id,
            self.number,
            self.version + REDEEMED_BYTE,
            REDEEMED_BYTE
        ):
            raise DomainException(ErrorKind.CONFLICT, "ticket redemption failed")


    def verify(self) -> bool:
        """
        Verify redemption of the current ticket.

        :return: redemption status
        """

        byte = ticket_storage.get_data_byte(self.event_id, self.number)

        if byte is None:
            return DomainException(ErrorKind.NOT_FOUND, "event not found")
        
        return byte >= REDEEMED_BYTE


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