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






## TODO - make this the replacement for data and fix everywhere
class EventSecrets(BaseModel):
    event_key: bytes = Field(default_factory=SKC.key, description="Ticket granting master key for event")
    owner_public_key: str = Field(..., description="Public key of event creator")



    @classmethod
    def load(self, event_id: str) -> "EventSecrets":
        """
        """
        
        secrets = event_db.load_secrets(event_id)

        if secrets is None:
            raise HTTPException(status_code=404, detail="Event data with associated ID not found")

        return self(**secrets)






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



    @staticmethod
    def delete(event_id: str) -> None:
        """
        """

        if not event_db.delete(event_id):
            raise HTTPException(404, detail="Event with associated ID not found")



    @classmethod
    def issue(self, event_id: str) -> "Event":
        """
        """
        
        event = event_db.issue(event_id)

        if event is None:
            raise HTTPException(status_code=404, detail="Event with associated ID not found")

        return self(**event)




    @classmethod
    def load(self, event_id: str) -> "Event":
        """
        """
        
        event = event_db.load_event(event_id)

        if event is None:
            raise HTTPException(status_code=404, detail="Event with associated ID not found")

        return self(**event)







    def create(self, owner_public_key: str) -> str:
        """

        :return: event ID
        """

        event_secrets = EventSecrets(owner_public_key=owner_public_key)
        event_db.create(self.model_dump(), event_secrets.model_dump())


        


    def next_ticket(self) -> int:
        """
        """

        return self.issued - 1
    




