"""
/transfer endpoint data packet models.

:author: Max Milazzo
"""



from app.API.models.base import Auth
from app.data.models.ticket import Ticket
from app.error.errors import ErrorKind, DomainException

from pydantic import BaseModel, Field
from typing import Self



class Transfer(BaseModel):
    """
    Transfer validation block signed by current ticket holder.
    """
    
    ticket: str = Field(..., description="Ticket being transferred")
    transfer_public_key: str = Field(
        ...,
        description="Public key of the new ticket owner (requesting user)"
    )



class TransferRequest(BaseModel):
    """
    /transfer user request.
    """

    event_id: str = Field(..., description="Event ID of the ticket being transferred")
    transfer: Auth[Transfer] = Field(
        ...,
        description="Transfer authorization block (signed by current ticket owner)"
    )



class TransferResponse(BaseModel):
    """
    /transfer server response.
    """
    
    ticket: str = Field(
        ...,
        description="Ticket string assigned to the new owner (requesting user)"
    )


    @classmethod
    def generate(cls, request: TransferRequest, public_key: str) -> Self:
        """
        Generate the server response from a user request.

        :param request: user request
        :param public_key: user public key
        :return: server response
        """

        transfer_data = request.transfer.unwrap()

        if transfer_data.transfer_public_key != public_key:
            raise DomainException(
                ErrorKind.PERMISSION,
                "authorization for different user"
            )
            # check that the transfer authorization is for the requesting user

        request.transfer.authenticate()
        # authenticate the transfer validation block
        
        old_ticket = Ticket.load(
            request.event_id,
            request.transfer.public_key,
            transfer_data.ticket
        )
        
        new_ticket = Ticket.reissue(
            request.event_id,
            public_key,
            old_ticket.number,
            old_ticket.version,
            old_ticket.transfer_limit,
            old_ticket.metadata
        )
        ticket = new_ticket.pack()

        return cls(ticket=ticket)