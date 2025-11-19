"""
/delete endpoint data packet models.

:author: Max Milazzo
"""



from app.data.models.event import Event
from app.data.models.permissions import Permissions
from app.error.errors import DomainException, ErrorKind

from pydantic import BaseModel, Field
from typing import Self



class DeleteRequest(BaseModel):
    """
    /delete user request.
    """
    
    event_id: str = Field(..., description="ID of the event to delete")



class DeleteResponse(BaseModel):
    """
    /delete server response.
    """

    success: bool = Field(..., description="Deletion status")


    @classmethod
    def generate(cls, request: DeleteRequest, public_key: str) -> Self:
        """
        Generate the server response from a user request.

        :param request: user request
        :param public_key: user public key
        :return: server response
        """

        if not Permissions.is_owner(request.event_id, public_key):
            raise DomainException(ErrorKind.PERMISSION, "not event owner")
            # confirm user is the event owner
        
        Event.delete(request.event_id)

        return cls(success=True)