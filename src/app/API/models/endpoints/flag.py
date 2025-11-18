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
    value: int | None = Field(
        None,
        ge=0,
        le=127,
        description="New flag value; omit to leave unchanged (for event owner only)"
    )
    public: bool | None = Field(
        False,
        description="Toggle public flag public visibility (for event owner only)"
    )



class FlagResponse(BaseModel):
    """
    /flag server response.
    """

    value: int = Field(..., description="Ticket flag value")
    is_public: bool = Field(..., description="Public flag public visibility")


    @classmethod
    def generate(cls, request: FlagRequest, public_key: str) -> Self:
        """
        Generate the server response from a user request.

        :param request: user request
        :return: server response
        """

        update_requested = (request.value is not None) or (request.public is not None)

        if update_requested:
            owner_public_key = Event.get_owner_public_key(request.event_id)

            if public_key != owner_public_key:
                raise DomainException(ErrorKind.PERMISSION, "not event owner")
                # ensure that any state update attempts come from the event owner

        ticket = Ticket.load(request.event_id, request.check_public_key, request.ticket)

        if update_requested:
            ticket.set_flag(request.value, request.public)
            value, is_public = request.value, request.public
        else:
            value, is_public = ticket.get_flag()

            if not is_public:
                owner_public_key = Event.get_owner_public_key(request.event_id)

                if owner_public_key != public_key:
                    raise DomainException(
                        ErrorKind.PERMISSION,
                        "ticket flag is not public"
                    )
                    # ensure that non-public flag state is only seen by the event owner

        return cls(value=value, is_public=is_public)