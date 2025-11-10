"""
/cancel endpoint data packet models.

:author: Max Milazzo
"""



from app.data.event import Event
from app.data.ticket import Ticket
from app.error.errors import ErrorKind, DomainException

from pydantic import BaseModel, Field
from typing import Self



class CancelRequest(BaseModel):
    """
    /cancel user request.
    """

    event_id: str = Field(..., description="Event ID of the ticket being canceled")
    ticket: str = Field(..., description="Ticket string to cancel")
    check_public_key: str = Field(..., description="Public key of the ticket holder")



class CancelResponse(BaseModel):
    """
    /cancel server response.
    """

    success: bool = Field(..., description="Ticket cancelation status")

    @classmethod
    def generate(cls, request: CancelRequest, public_key: str) -> Self:
        """
        Generate the server response from a user request.

        :param request: user request
        :return: server response
        """

        owner_public_key = Event.get_owner_public_key(request.event_id)

        if owner_public_key != public_key:
            raise DomainException(ErrorKind.PERMISSION, "not event owner")
            # confirm user is the event owner (via recorded public key)

        ticket = Ticket.load(request.event_id, request.check_public_key, request.ticket)
        ticket.cancel()

        return cls(success=True)