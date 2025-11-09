"""
/delete endpoint data packet models.

:author: Max Milazzo
"""



from app.data.event import Event
from app.error.errors import ErrorKind, DomainException

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

        owner_public_key = Event.get_owner_public_key(request.event_id)

        if owner_public_key != public_key:
            raise DomainException(ErrorKind.PERMISSION, "not event owner")
            # confirm user is the event owner (via recorded public key)
        
        Event.delete(request.event_id)

        return cls(success=True)