from .base import Auth
from fastapi import HTTPException
from pydantic import BaseModel, Field
from app.data.event import EventData
from app.data import event
from typing import Optional, List

from app.data.ticket import Ticket

class RegisterRequest(BaseModel):
    event_id: str = Field(..., description="ID of event to register for")
    verification: Optional[Auth[str]] = Field(None, description="Verification for non-public/paid events (user public key signed by event owner)")

    def to_dict(self) -> dict:

        if self.verification is None:
            verif_value = None
        else:
            verif_value = self.verification.to_dict()

        return {
            "event_id": self.event_id,
            "verification": verif_value
        }


class RegisterResponse(BaseModel):
    ticket: str = Field(..., description="Ticket string of registered user")

    @classmethod
    def generate(self, request: RegisterRequest, public_key: str) -> "RegisterResponse":
        """
        """

        event_data = EventData.load(request.event_id)

        if event_data.event.private:
            if request.verification is None:
                raise HTTPException(status_code=401, detail="No authorization")
            
            if request.verification.public_key != event_data.data.owner_public_key:
                raise HTTPException(status_code=401, detail="Authorization key incorrect")
            
            if request.verification.unwrap() != public_key:
                raise HTTPException(status_code=401, detail="Authorization for incorrect key")

            request.verification.authenticate()
            
        ticket = Ticket.register(request.event_id, public_key)
        ticket = ticket.pack()

        return self(ticket=ticket)

    
    def to_dict(self) -> dict:
        return self.__dict__