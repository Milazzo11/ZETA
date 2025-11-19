"""
/flag endpoint data packet models.

:author: Max Milazzo
"""



from app.data.models.permissions import Permissions
from app.data.models.ticket import Ticket, FLAG_PUBLIC_TOGGLE_BYTE
from app.error.errors import ErrorKind, DomainException

from pydantic import BaseModel, Field
from typing import Self



class FlagRequest(BaseModel):
    """
    /flag user request.
    """

    event_id: str = Field(..., description="Event ID of the flagged ticket")
    ticket_number: int = Field(..., description="Flagged ticket number")
    value: int | None = Field(
        None,
        ge=0,
        le=FLAG_PUBLIC_TOGGLE_BYTE - 1,
        description="New flag value; omit to leave unchanged (for event owner only)"
    )
    public: bool | None = Field(
        False,
        description="Toggle public flag visibility (for event owner only)"
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

        if (request.value is None) != (request.public is None):
            raise DomainException(
                ErrorKind.VALIDATION, 
                "'value' and 'public' fields must be supplied together"
            )
            # ensure that value and public fields are either both set or both unset

        if request.value is not None:
            permissions = Permissions.load(request.event_id, public_key)
            
            if not permissions.is_authorized("update_ticket_flag"):
                raise DomainException(ErrorKind.PERMISSION, "permission denied")
                # ensure that any state update attempts come from the event owner

            Ticket.set_flag(
                request.event_id,
                request.ticket_number,
                request.value,
                request.public
            )
            value, is_public = request.value, request.public

        else:
            value, is_public = Ticket.get_flag(request.event_id, request.ticket_number)

            if not is_public:
                permissions = Permissions.load(request.event_id, public_key)

                if not permissions.is_authorized("see_ticket_flag"):
                    raise DomainException(
                        ErrorKind.PERMISSION,
                        "ticket flag is not public"
                    )
                    # ensure that non-public flag state is only seen by the event owner

        return cls(value=value, is_public=is_public)