"""
"""


import time
import uuid
from config import DEFAULT_EVENT_TTL, DEFAULT_EVENT_TICKETS
from pydantic import BaseModel, Field
from typing import List, Optional, Tuple, Union

from app.crypto.symmetric import SKC

from fastapi import HTTPException

from .storage import event as event_db





class Data(BaseModel):
    event_key: bytes = Field(default_factory=SKC.key, description="Ticket granting master key for event")
    owner_public_key: str = Field(..., description="Public key of event creator")






class Event(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Event ID")
    name: str = Field(..., description="Event name")
    description: str = Field(..., description="Event description")
    tickets: int = Field(DEFAULT_EVENT_TICKETS, description="Number of total event tickets")
    issued: int = Field(0, description="Number of tickets issued")
    start: float = Field(default_factory=lambda: time.time(), description="Epoch timestamp of event start date")
    finish: float = Field(default_factory=lambda: time.time() + DEFAULT_EVENT_TTL, description="Epoch timestamp of event end date")
    restricted: bool = Field(False, description="Specifies whether event is open or restricted (requires authorization)")
    # TODO - set contstriants on these values
    ## also: the select * always loading style into event doesn't seem sustainable -- but db is just poc? well idk
    ## (at most prob just make a command that specific targeted fields could add marginal efficicney)
    ## TODO * some comments here prob bs (just make note of contraint possibility -- not rly in scope here imo and poss client side tbh)

    ## TODO* change name from private to restricted/controlled or sum

    ## TODO* I think this isnt needed -- obj = MyModel.parse_obj(data) load from dict




    @staticmethod
    def search(text: str, limit: int) -> List["Event"]:
        """
        """

        raw_data = event_db.search(text, limit)
        data_list = []

        for event_dict in raw_data:
            data_list.append(Event(**event_dict))

        return data_list









    @classmethod
    def load(self, event_id: str) -> "Event":
        """
        """
        
        dict = event_db.load(event_id)

        if dict is None:
            raise HTTPException(status_code=404, detail="Event with associated ID not found")

        return self(**dict)







    def create(self, owner_public_key: str) -> str:
        """

        :return: event ID
        """

        event_data = Data(owner_public_key=owner_public_key)
        event_db.create(self.model_dump(), event_data.model_dump())


    def next_ticket(self) -> int:
        """
        """

        return self.issued - 1








class EventData(BaseModel):
    event: Event = Field(..., description="User-facing event packet")
    data: Data = Field(..., description="Event data")



    @staticmethod
    def delete(event_id: str) -> None:
        """
        """

        if not event_db.delete(event_id):
            raise HTTPException(404, detail="Event with associated ID not found")


    @classmethod
    def load(self, event_id: str, issue: bool = False) -> "EventData":
        """
        """

        dict = event_db.load_full(event_id, issue=issue)

        
        if dict is None:
            if issue:
                raise HTTPException(status_code=410, detail="All tickets registered")

            raise HTTPException(status_code=404, detail="Event with associated ID not found")
        
        return self(
            event=Event(**dict["event"]),
            data=Data(**dict["data"])
        )
    



    def next_ticket(self) -> int:
        return self.event.next_ticket()





