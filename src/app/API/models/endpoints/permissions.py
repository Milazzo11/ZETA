"""
/permissions endpoint data packet models.

:author: Max Milazzo
"""



from app.data.models.permissions import Permissions
from app.data.models.ticket import Ticket
from app.error.errors import ErrorKind, DomainException

from pydantic import BaseModel, Field
from typing import Self







class PermissionsRequest(BaseModel):
    """
    /permissions user request.
    """

    event_id: str = Field(..., description="ID of the event to access permissions for")
    target_public_key: str = Field(
        ...,
        description="Public key of the user whose permissions are being accessed"
    )
    permissions: Permissions | None = Field(
        ...,
        description="Permissions to apply for the target user; omit to leave unchanged"
    )


class PermissionsResponse(BaseModel):
    """
    /permissions server response.
    """

    permissions: Permissions = Field(..., description="User permissions")

    
    @classmethod
    def generate(cls, request: PermissionsRequest, public_key: str) -> Self:
        """
        Generate the server response from a user request.

        :param request: user request
        :return: server response
        """

        # make an Event.GetPermissions

        return cls()