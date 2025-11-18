"""
/validate endpoint data packet models.

:author: Max Milazzo
"""



from app.data.models.event import Event, TRANSFER_LIMIT
from app.data.models.ticket import Ticket
from app.error.errors import ErrorKind, DomainException

from pydantic import BaseModel, Field
from typing import Any, Self



class ValidateRequest(BaseModel):
    """
    /validate user request.
    """

    event_id: str = Field(..., description="Event ID of the ticket being validated")
    ticket: str = Field(..., description="Ticket string being validated")
    check_public_key: str = Field(..., description="Public key of the ticket holder")
    stamp: bool = Field(
        False,
        description="If true, mark the ticket as used (for event owner only)"
    )



class ValidateResponse(BaseModel):
    """
    /validate server response.
    """

    redeemed: bool = Field(..., description="User ticket redemption status")
    stamped: bool | None = Field(
        ...,
        description="If true, ticket is stamped (for event owner only)"
    )
    version: int = Field(
        ...,
        ge=1,
        le=TRANSFER_LIMIT + 1,
        description="Ticket transfer version"
    )
    transfer_limit: int = Field(
        ...,
        ge=0,
        le=TRANSFER_LIMIT,
        description="ticket transfer limit"
    )
    metadata: Any = Field(..., description="Ticket metadata")


    @classmethod
    def generate(cls, request: ValidateRequest, public_key: str) -> Self:
        """
        Generate the server response from a user request.

        :param request: user request
        :return: server response
        """

        is_ticket_holder = (request.check_public_key == public_key)
        is_event_owner = False

        if not is_ticket_holder or request.stamp:
            owner_public_key = Event.get_owner_public_key(request.event_id)
            is_event_owner = (owner_public_key == public_key)
            
            if request.stamp and not is_event_owner:
                raise DomainException(
                    ErrorKind.PERMISSION,
                    "only event owners may stamp tickets"
                )
                # ensure that any ticket stamp attempts come from the event owner

        ticket = Ticket.load(request.event_id, request.check_public_key, request.ticket)

        if request.stamp:
            ticket.stamp()
            redeemed, stamped = True, True
        else:
            redeemed, stamped = ticket.verify()

        if not (is_ticket_holder or is_event_owner):
            stamped = None

        return cls(
            redeemed=redeemed,
            stamped=stamped,
            version=ticket.version + 1,  # 1-indexed version
            transfer_limit=ticket.transfer_limit,
            metadata=ticket.metadata
        )