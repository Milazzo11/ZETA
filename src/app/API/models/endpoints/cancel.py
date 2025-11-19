"""
/cancel endpoint data packet models.

:author: Max Milazzo
"""



from app.data.models.permissions import Permissions
from app.data.models.event import TICKET_LIMIT, TRANSFER_LIMIT
from app.data.models.ticket import Ticket
from app.error.errors import ErrorKind, DomainException

from pydantic import BaseModel, Field
from typing import Self



class CancelRequest(BaseModel):
    """
    /cancel user request.
    """

    event_id: str = Field(..., description="Event ID of the ticket being canceled")
    ticket_number: int = Field(
        ...,
        ge=1,
        le=TICKET_LIMIT,
        description="Ticket number to cancel"
    )
    audit_flag: int = Field(
        0,
        ge=0,
        le=TRANSFER_LIMIT,
        description="Flag value to record for cancellation auditing"
    )



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

        permissions = Permissions.load(request.event_id, public_key)

        if not permissions.is_authorized("cancel_ticket"):
            raise DomainException(ErrorKind.PERMISSION, "permission denied")
            # confirm user is an authorized party

        Ticket.cancel(
            request.event_id,
            request.ticket_number - 1, # 0-indexed ticket number
            request.audit_flag
        )

        return cls(success=True)