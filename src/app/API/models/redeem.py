
from fastapi import HTTPException
from app.data.event import Event
from typing import List, Union, Generic, TypeVar, Optional
from pydantic import BaseModel, Field

from app.data.ticket import Ticket


class RedeemRequest(BaseModel):
    event_id: str = Field(..., description="ID of the event for which the ticket is being redeemed")
    ticket: str = Field(..., description="Ticket being redeemed")

    def to_dict(self) -> dict:
        return self.__dict__



class RedeemResponse(BaseModel):
    success: bool = Field(True, description="Ticket redemption status")

    @classmethod
    def generate(self, request: RedeemRequest, public_key: str) -> "RedeemResponse":
        """
        """

        ticket = Ticket.load(request.event_id, public_key, request.ticket)
        ticket.redeem()

        return self(success=True)
    
    
    def to_dict(self) -> dict:
        return self.__dict__