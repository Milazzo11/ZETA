"""
/verify endpoint data packet models.

:author: Max Milazzo
"""



from app.data.ticket import Ticket

from pydantic import BaseModel, Field
from typing import Optional, Self



class VerifyRequest(BaseModel):
    """
    /verify user request.
    """

    event_id: str = Field(..., description="Event ID of the ticket being verified")
    ticket: str = Field(..., description="Ticket string being verified")
    check_public_key: str = Field(..., description="Public key of the ticket holder")



class VerifyResponse(BaseModel):
    """
    /verify server response.
    """

    verification: bool = Field(..., description="User ticket redemption status")
    metadata: Optional[str] = Field(..., description="Ticket metadata")


    @classmethod
    def generate(cls, request: VerifyRequest) -> Self:
        """
        Generate the server response from a user request.

        :param request: user request
        :return: server response
        """

        ticket = Ticket.load(request.event_id, request.check_public_key, request.ticket)
        verification = ticket.verify()

        return cls(verification=verification, metadata=ticket.metadata)