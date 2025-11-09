"""
Event data model.

:author: Max Milazzo
"""



from .storage import event as event_storage
from app.crypto.symmetric import SKC
from app.error.errors import ErrorKind, DomainException

import time
import uuid
from pydantic import BaseModel, Field
from typing import List, Self



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


    @staticmethod
    def get_key(event_id: str) -> bytes:
        """
        Get event symmetric ticket encryption key.

        :param event_id: unique event identifier
        :return: event key
        """

        key = event_storage.load_event_key(event_id)

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

        public_key = event_storage.load_owner_public_key(event_id)

        if public_key is None:
            raise DomainException(ErrorKind.NOT_FOUND, "event not found")
        
        return public_key
    

    @staticmethod
    def delete(event_id: str) -> None:
        """
        Delete an event.

        :param event_id: unique event identifier
        """

        event_storage.delete(event_id)
    

    @classmethod
    def load(cls, event_id: str) -> Self:
        """
        Load an event.

        :param event_id: unique event identifier
        :return: event model
        """
        
        event = event_storage.load_event(event_id)

        if event is None:
            raise DomainException(ErrorKind.NOT_FOUND, "event not found")

        return cls(**event)


    @classmethod
    def search(cls, text: str, limit: int) -> List[Self]:
        """
        Search for an event.

        :param text: text search pattern
        :param limit: query fetch limit
        :return: list of matching events
        """

        rows = event_storage.search(text, limit)
        
        return [cls(**row) for row in rows]


    def create(self, owner_public_key: str) -> None:
        """
        Create an event.

        :param owner_public_key: public key of the event creator (owner)
        """

        event_storage.create(self.model_dump(), SKC.key(), owner_public_key)