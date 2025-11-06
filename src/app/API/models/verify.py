"""
/verify endpoint data packet models.

:author: Max Milazzo
"""


from app.data.ticket import Ticket

from pydantic import BaseModel, Field
from typing import Optional


class VerifyRequest(BaseModel):
    """
    /verify user request.
    """

    event_id: str = Field(..., description="ID of the event to check user verification for")
    ticket: str = Field(..., description="Ticket string of user to check")
    check_public_key: str = Field(..., description="Public key of the user being checked for ticket redemption")



class VerifyResponse(BaseModel):
    """
    /verify server response.
    """

    verification: bool = Field(..., description="User ticket redemption status")
    metadata: Optional[str] = Field(..., description="Ticket metadata")

    @classmethod
    def generate(self, request: VerifyRequest) -> "VerifyResponse":
        """
        Generate the server response from a user request.

        :param request: user request
        :return: server response
        """

        ticket = Ticket.load(request.event_id, request.check_public_key, request.ticket)
        verification = ticket.verify()

        return self(verification=verification, metadata=ticket.metadata)
