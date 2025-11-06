"""
/register endpoint data packet models.

:author: Max Milazzo
"""



from .base import Auth
from app.data.event import EventData
from app.data.ticket import Ticket

from fastapi import HTTPException
from pydantic import BaseModel, Field
from typing import Optional



class Verification(BaseModel):
    event_id: str = Field(..., description="ID of event to register for")
    public_key: str = Field(..., description="Public key of user registering")
    metadata: Optional[str] = Field(None, description="Custom ticket metadata")


class RegisterRequest(BaseModel):
    """
    /register user request.
    """

    event_id: str = Field(..., description="ID of event to register for")
    verification: Optional[Auth[Verification]] = Field(None, description="Verification for non-public/paid events")


class RegisterResponse(BaseModel):
    """
    /register server response.
    """

    ticket: str = Field(..., description="Ticket string of registered user")

    @classmethod
    def generate(self, request: RegisterRequest, public_key: str) -> "RegisterResponse":
        """
        Generate the server response from a user request.

        :param request: user request
        :param public_key: user public key
        :return: server response
        """

        event_data = EventData.load(request.event_id)##TODO-maybe move these event data checks in ticket class
        metadata = None

        if event_data.event.private:
            if request.verification is None:
                raise HTTPException(status_code=401, detail="No authorization")
            
            if request.verification.public_key != event_data.data.owner_public_key:
                raise HTTPException(status_code=401, detail="Authorization key incorrect")
            
            verif_data = request.verification.unwrap()

            if verif_data.event_id != request.event_id:
                raise HTTPException(status_code=401, detail="Authorization for incorrect event")
            
            if verif_data.public_key != public_key:
                raise HTTPException(status_code=401, detail="Authorization for incorrect key")

            request.verification.authenticate()
            metadata = verif_data.metadata
            
        ticket = Ticket.register(request.event_id, public_key, metadata=metadata)

        print(ticket.number)
        ticket = ticket.pack()

        return self(ticket=ticket)