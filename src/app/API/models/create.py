"""
/event endpoint data packet models.

:author: Max Milazzo
"""



from app.data.event import Event

from pydantic import BaseModel, Field
from typing import Self



class CreateRequest(BaseModel):
    """
    /create user request.
    """

    event: Event = Field(..., description="New event to create on server")
    


class CreateResponse(BaseModel):
    """
    /create server response.
    """

    event_id: str = Field(..., description="New event ID")


    @classmethod
    def generate(cls, request: CreateRequest, public_key: str) -> Self:
        """
        Generate the server response from a user request.

        :param request: user request
        :param public_key: user public key
        :return: server response
        """

        request.event.create(public_key)

        return cls(event_id=request.event.id)