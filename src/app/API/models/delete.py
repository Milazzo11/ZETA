"""
/delete endpoint data packet models.

:author: Max Milazzo
"""



from app.data.event import Event, EventSecrets

from fastapi import HTTPException
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

        event_secrets = EventSecrets.load(request.event_id)

        if event_secrets.owner_public_key != public_key:
            raise HTTPException(
                status_code=401,
                detail="Only an event owner may delete his own event"
            )
            # confirm user is the event owner (via recorded public key)
        
        Event.delete(request.event_id)

        return cls(success=True)