"""
/flag endpoint data packet models.

:author: Max Milazzo
"""



from app.data.models.event import Event
from app.data.models.ticket import Ticket
from app.error.errors import ErrorKind, DomainException

from pydantic import BaseModel, Field
from typing import Self



class FlagRequest(BaseModel):
    """
    /flag user request.
    """

    event_id: str = Field(..., description="Event ID of the flagged ticket")
    ticket: str = Field(..., description="Flagged ticket string")
    check_public_key: str = Field(..., description="Public key of the ticket holder")
    set: int | None = Field(
        None,
        ge=0,
        le=255,
        description="New flag value; omit to leave unchanged"
    )



class FlagResponse(BaseModel):
    """
    /flag server response.
    """

    flag: int = Field(..., description="Ticket flag value")


    @classmethod
    def generate(cls, request: FlagRequest, public_key: str) -> Self:
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

        if request.set is None:
            flag = ticket.get_flag()
        else:
            ticket.set_flag(request.set)
            flag = request.set

        return cls(flag=flag)