
from pydantic import BaseModel, Field

from app.data.ticket import Ticket

from fastapi import HTTPException


class CancelRequest(BaseModel):
    event_id: str = Field(..., description="ID of the event for which the ticket is being returned")
    ticket: str = Field(..., description="Ticket being returned")

    def to_dict(self) -> dict:
        return self.__dict__


class CancelResponse(BaseModel):
    success: bool = Field(True, description="Ticket cancellation status")

    @classmethod
    def generate(self, request: CancelRequest, public_key: str) -> "CancelResponse":
        """
        """

        ticket = Ticket.load(request.event_id, public_key, request.ticket)
        ticket.cancel()

        return self(success=True)
    
    def to_dict(self) -> dict:
        return self.__dict__