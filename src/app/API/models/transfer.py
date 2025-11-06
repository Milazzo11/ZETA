"""
/transfer endpoint data packet models.

:author: Max Milazzo
"""


from .base import Auth
from app.data.ticket import Ticket

from fastapi import HTTPException
from pydantic import BaseModel, Field


class Transfer(BaseModel):
    ticket: str = Field(..., description="Ticket being transferred")
    transfer_public_key: str = Field(..., description="Public key of the new ticket owner (user making request)")


class TransferRequest(BaseModel):
    """
    /transfer user request.
    """

    event_id: str = Field(..., description="ID of the event for which the ticket is being transferred")
    transfer: Auth[Transfer] = Field(..., description="Transfer authorization JSON (signed by current ticket owner)")



class TransferResponse(BaseModel):
    """
    /transfer server response.
    """
    
    ticket: str = Field(..., description="New ticket string transferred to user")

    @classmethod
    def generate(self, request: TransferRequest, public_key: str) -> "TransferResponse":
        """
        Generate the server response from a user request.

        :param request: user request
        :param public_key: user public key
        :return: server response
        """

        transfer_data = request.transfer.unwrap()

        if transfer_data.transfer_public_key != public_key:
            raise HTTPException(status_code=400, detail="Authorization key incorrect")
        
        old_ticket = Ticket.load(request.event_id, request.transfer.public_key, transfer_data.ticket)
        request.transfer.authenticate()

        new_ticket = Ticket.reissue(
            request.event_id, public_key, number=old_ticket.number,
            version=old_ticket.version, metadata=old_ticket.metadata
        )
        ticket = new_ticket.pack()

        return self(ticket=ticket)