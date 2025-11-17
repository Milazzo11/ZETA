"""
/register endpoint data packet models.

:author: Max Milazzo
"""



from app.API.models.base import Auth
from app.data.models.event import Event, TRANSFER_LIMIT
from app.data.models.ticket import Ticket
from app.error.errors import ErrorKind, DomainException

from pydantic import BaseModel, Field
from typing import Any, Self



class Verification(BaseModel):
    """
    Registration verification block signed by event owner.
    """

    event_id: str = Field(..., description="ID of the event to register for")
    public_key: str = Field(..., description="Public key of the registering user")
    transfer_limit: int | None = Field(
        None,
        ge=0,
        le=TRANSFER_LIMIT,
        description="Custom ticket transfer limit"
    )
    metadata: Any = Field(None, description="Custom ticket metadata")



class RegisterRequest(BaseModel):
    """
    /register user request.
    """

    event_id: str = Field(..., description="ID of the event to register for")
    verification: Auth[Verification] | None = Field(
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

        transfer_limit = event.transfer_limit
        metadata = None

        if event.restricted:
            if request.verification is None:
                raise DomainException(ErrorKind.PERMISSION, "verification required")
                # confirm verification provided
            
            verif_data = request.verification.unwrap()

            if verif_data.event_id != request.event_id:
                raise DomainException(
                    ErrorKind.PERMISSION,
                    "verification for different event"
                )
                # confirm verification is for the correct event
            
            if verif_data.public_key != public_key:
                raise DomainException(
                    ErrorKind.PERMISSION,
                    "verification for different user"
                )
                # confirm verification is for the requesting user

            owner_public_key = Event.get_owner_public_key(request.event_id)

            if request.verification.public_key != owner_public_key:
                raise DomainException(ErrorKind.PERMISSION, "unauthorized signer")
                # confirm verification is signed by the event owner

            request.verification.authenticate()
            # authenticate verification block

            if verif_data.transfer_limit is not None:
                transfer_limit = verif_data.transfer_limit

            metadata = verif_data.metadata
        
        ticket = Ticket.register(request.event_id, public_key, transfer_limit, metadata)
        ticket = ticket.pack()

        return cls(ticket=ticket)