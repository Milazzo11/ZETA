"""
Event data model.

:author: Max Milazzo
"""



from app.data.storage import event_store
from app.crypto.symmetric import SKC
from app.error.errors import ErrorKind, DomainException

import time
import uuid
from pydantic import BaseModel, Field
from typing import Self



TRANSFER_LIMIT = 1 << 6 - 1
# transfer limit value: 0b00111111
# (transfer version data stored in low 6 bits)



class Event(BaseModel):
    """
    Public-facing event data model.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Event ID")
    name: str = Field(..., description="Event name")
    description: str = Field(..., description="Event description")
    tickets: int = Field(128, ge=1, le=65_536, description="Number of total event tickets")
    issued: int = Field(0, ge=0, le=65_536, description="Number of tickets issued")
    start: float = Field(
        default_factory=lambda: time.time(),
        description="Epoch timestamp of event start date"
    )
    finish: float = Field(
        default_factory=lambda: time.time() + 86_400,
        description="Epoch timestamp of event end date"
    )
    restricted: bool = Field(
        False,
        description="Specifies whether event is open or restricted (requires authorization)"
    )
    transfer_limit: int = Field(
        TRANSFER_LIMIT,
        ge=0,
        le=TRANSFER_LIMIT,
        description="Default maximum number of allowed ticket transfers"
    )


    @staticmethod
    def get_key(event_id: str) -> bytes:
        """
        Get event symmetric ticket encryption key.

        :param event_id: unique event identifier
        :return: event key
        """

        key = event_store.load_event_key(event_id)

        if key is None:
            raise DomainException(ErrorKind.NOT_FOUND, "event not found")
        
        return key


    @staticmethod
    def get_owner_public_key(event_id: str) -> str:
        """
        Get event owner public key.

        :param event_id: unique event identifier
        :return: event owner public key
        """

        public_key = event_store.load_owner_public_key(event_id)

        if public_key is None:
            raise DomainException(ErrorKind.NOT_FOUND, "event not found")
        
        return public_key
    

    @staticmethod
    def delete(event_id: str) -> None:
        """
        Delete an event.

        :param event_id: unique event identifier
        """

        if not event_store.delete(event_id):
            raise DomainException(ErrorKind.NOT_FOUND, "event not found")


    @classmethod
    def load(cls, event_id: str) -> Self:
        """
        Load an event.

        :param event_id: unique event identifier
        :return: event model
        """
        
        event = event_store.load_event(event_id)

        if event is None:
            raise DomainException(ErrorKind.NOT_FOUND, "event not found")

        return cls(**event)


    @classmethod
    def search(cls, text: str, limit: int) -> list[Self]:
        """
        Search for an event.

        :param text: text search pattern
        :param limit: query fetch limit
        :return: list of matching events
        """

        rows = event_store.search(text, limit)
        
        return [cls(**row) for row in rows]


    def create(self, owner_public_key: str) -> None:
        """
        Create an event.

        :param owner_public_key: public key of the event creator (owner)
        """

        event_store.create(self.model_dump(), SKC.key(), owner_public_key)