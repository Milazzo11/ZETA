"""
"""


import time
import uuid
from config import DEFAULT_EVENT_TTL, DEFAULT_EVENT_TICKETS, DEFAULT_EXCHANGES
from pydantic import BaseModel, Field
from typing import List, Optional, Tuple, Union

from app.crypto.symmetric import SKE

from fastapi import HTTPException

from .storage import event as event_db





class Data(BaseModel):
    event_key: bytes = Field(default_factory=SKE.key, description="Ticket granting master key for event")
    owner_public_key: str = Field(..., description="Public key of event creator")

    @classmethod
    def from_dict(self, data: dict) -> "Data":
        return self(
            event_key=data.get("event_key", SKE.key()),
            owner_public_key=data["owner_public_key"],  # This must be provided
        )


    def to_dict(self) -> dict:
        return self.__dict__




class Event(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Event ID")
    name: str = Field(..., description="Event name")
    description: str = Field(..., description="Event description")
    tickets: int = Field(DEFAULT_EVENT_TICKETS, description="Number of total event tickets")
    issued: int = Field(0, description="Number of tickets issued")
    start: float = Field(default_factory=lambda: time.time(), description="Epoch timestamp of event start date")
    end: float = Field(default_factory=lambda: time.time() + DEFAULT_EVENT_TTL, description="Epoch timestamp of event end date")
    private: bool = Field(False, description="Specifies whether event is public (open) or private (requires authorization)")
    # TODO - set contstriants on these values
    ## also: the select * always loading style into event doesn't seem sustainable -- but db is just poc? well idk
    ## (at most prob just make a command that specific targeted fields could add marginal efficicney)
    ## TODO * some comments here prob bs (just make note of contraint possibility -- not rly in scope here imo and poss client side tbh)


    @classmethod
    def from_dict(self, data: dict) -> "Event":
        # Manually set default values if not provided in the dictionary

        return self(
            id=data.get("id", str(uuid.uuid4())),
            name=data["name"],  # This must be provided
            description=data["description"],  # This must be provided
            tickets=data.get("tickets", DEFAULT_EVENT_TICKETS),
            issued=data.get("issued", 0),
            start=data.get("start", time.time()),
            end=data.get("end", time.time() + DEFAULT_EVENT_TTL),
            private=data.get("private", False),
        )




    @classmethod
    def load(self, event_id: str) -> "Event":
        """
        """
        
        dict = event_db.load(event_id)
        return self.from_dict(dict)






    def to_dict(self) -> dict:
        return self.__dict__



    def create(self, owner_public_key: str) -> str:
        """

        :return: event ID
        """

        event_data = Data(owner_public_key=owner_public_key)
        event_db.create(self.to_dict(), event_data.to_dict())


    def next_ticket(self) -> int:
        """
        """

        if self.issued > self.tickets:
            raise HTTPException(status_code=401, detail="All tickets registered")
        
        return self.issued - 1








class EventData(BaseModel):
    event: Event = Field(..., description="User-facing event packet")
    data: Data = Field(..., description="Event data")


    @classmethod
    def load(self, event_id: str, issue: bool = False) -> "EventData":
        """
        """

        dict = event_db.load_full(event_id, issue=issue)

        print(dict)

        return self(
            event=Event.from_dict(dict["event"]),
            data=Data.from_dict(dict["data"])
        )
    

    @classmethod
    def from_dict(self, dict) -> "EventData":
        self.event = Event.from_dict(dict["event"])
        self.data = Data.from_dict(dict["data"])


    def to_dict(self) -> dict:
        return {
            "event": self.event.to_dict(),
            "data": self.event.to_dict()
        }
    

    def next_ticket(self) -> int:
        return self.event.next_ticket()





def search(text: str, limit: int) -> List[Event]:
    """
    """

    raw_data = event_db.search(text, limit)
    data_list = []

    for event_dict in raw_data:
        data_list.append(Event.from_dict(event_dict))

    return data_list