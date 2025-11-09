"""
Event data models.

:author: Max Milazzo
"""



from .storage import event as event_storage
from app.crypto.symmetric import SKC

import time
import uuid
from pydantic import BaseModel, Field
from typing import List, Self



class EventSecrets(BaseModel):
    """
    Non-public-facing event data model.
    """

    event_key: bytes = Field(
        default_factory=SKC.key,
        description="Ticket granting master key for event"
    )
    owner_public_key: str = Field(..., description="Public key of event creator")


    @classmethod
    def load(cls, event_id: str) -> Self:
        """
        Load event secrets from database.

        :param event_id: ID of the event to load secrets from
        :return: event secrets
        """
        
        secrets = event_storage.load_secrets(event_id)

        return cls(**secrets)



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
    def search(text: str, limit: int) -> List[Self]:
        """
        Search for an event.

        :param text: text search pattern
        :param limit: query fetch limit
        :return: list of matching events
        """

        raw_data = event_storage.search(text, limit)
        data_list = []

        for event_dict in raw_data:
            data_list.append(Event(**event_dict))

        return data_list


    @staticmethod
    def issue(cls, event_id: str) -> int:
        """
        Issue a ticket for an event.

        :param event_id: ID of the event to issue for
        :return: issued ticket number
        """
        
        event = event_storage.issue(event_id)

        return event["issued"] - 1


    @staticmethod
    def delete(event_id: str) -> None:
        """
        Delete an event.

        :param event_id: ID of the event to delete
        """

        event_storage.delete(event_id)


    @classmethod
    def load(cls, event_id: str) -> Self:
        """
        Load an event.

        :param event_id: ID of the event to load
        :return: event
        """
        
        event = event_storage.load_event(event_id)

        return cls(**event)


    def create(self, owner_public_key: str) -> str:
        """
        Create an event

        :param owner_public_key: public key of the event creator (owner)
        :return: ID of the new event
        """

        event_secrets = EventSecrets(owner_public_key=owner_public_key)
        event_storage.create(self.model_dump(), event_secrets.model_dump())