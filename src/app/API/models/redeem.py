"""
/redeem endpoint data packet models.

:author: Max Milazzo
"""



from app.data.ticket import Ticket

from pydantic import BaseModel, Field
from typing import Self



class RedeemRequest(BaseModel):
    """
    /redeem user request.
    """

    event_id: str = Field(..., description="Event ID of the ticket being redeemed")
    ticket: str = Field(..., description="Ticket being redeemed")



class RedeemResponse(BaseModel):
    """
    /redeem server response.
    """

    success: bool = Field(..., description="Ticket redemption status")


    @classmethod
    def generate(cls, request: RedeemRequest, public_key: str) -> Self:
        """
        Generate the server response from a user request.

        :param request: user request
        :param public_key: user public key
        :return: server response
        """

        ticket = Ticket.load(request.event_id, public_key, request.ticket)
        ticket.redeem()

        return cls(success=True)