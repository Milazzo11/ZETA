from pydantic import BaseModel, Field
from app.data.event import Event
from typing import List, Optional
from fastapi import HTTPException

from app.data.ticket import Ticket


class VerifyRequest(BaseModel):
    event_id: str = Field(..., description="ID of the event to check user verification for")
    ticket: str = Field(..., description="Ticket string of user to check")
    check_public_key: str = Field(..., description="Public key of the user being checked for ticket redemption")

    def to_dict(self) -> dict:
        return self.__dict__



class VerifyResponse(BaseModel):
    verification: bool = Field(True, description="User ticket redemption status")

    @classmethod
    def generate(self, request: VerifyRequest, public_key: str) -> "VerifyResponse":
        """
        """

        ticket = Ticket.load(request.event_id, public_key, request.ticket)
        verification = ticket.verify()

        return self(verification=verification)
    

    def to_dict(self) -> dict:
        return self.__dict__