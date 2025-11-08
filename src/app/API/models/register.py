"""
/register endpoint data packet models.

:author: Max Milazzo
"""



from .base import Auth
from app.data.event import Event, EventSecrets
from app.data.ticket import Ticket

from fastapi import HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Self



class Verification(BaseModel):
    """
    Registration verification block signed by event owner.
    """

    event_id: str = Field(..., description="ID of the event to register for")
    public_key: str = Field(..., description="Public key of the registering user")
    metadata: Optional[str] = Field(None, description="Custom ticket metadata")



class RegisterRequest(BaseModel):
    """
    /register user request.
    """

    event_id: str = Field(..., description="ID of the event to register for")
    verification: Optional[Auth[Verification]] = Field(
        None,
        description="Verification for restricted events"
    )


class RegisterResponse(BaseModel):
    """
    /register server response.
    """

    ticket: str = Field(..., description="Ticket string of registered user")


    @classmethod
    def generate(cls, request: RegisterRequest, public_key: str) -> Self:
        """
        Generate the server response from a user request.

        :param request: user request
        :param public_key: user public key
        :return: server response
        """

        event = Event.load(request.event_id)
        event_secrets = EventSecrets.load(request.event_id)

        metadata = None

        if event.restricted:
            if request.verification is None:
                raise HTTPException(status_code=401, detail="No authorization")
                # confirm verification provided
            
            if request.verification.public_key != event_secrets.owner_public_key:
                raise HTTPException(status_code=401, detail="Authorization key incorrect")
                # confirm verification is signed by the event owner
            
            verif_data = request.verification.unwrap()

            if verif_data.event_id != request.event_id:
                raise HTTPException(status_code=401, detail="Authorization for incorrect event")
                # confirm verification is for the correct event
            
            if verif_data.public_key != public_key:
                raise HTTPException(status_code=401, detail="Authorization for incorrect key")
                # confirm verification is for the requesting user

            request.verification.authenticate()
            # authenticate verification block

            metadata = verif_data.metadata
            
        ticket = Ticket.register(request.event_id, public_key, metadata=metadata)
        ticket = ticket.pack()

        return cls(ticket=ticket)