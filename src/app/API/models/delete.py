
from fastapi import HTTPException
from app.data.event import EventData
from typing import List, Union, Generic, TypeVar, Optional
from pydantic import BaseModel, Field

from app.data.ticket import Ticket


class DeleteRequest(BaseModel):
    event_id: str = Field(..., description="ID of the event to delete")


class DeleteResponse(BaseModel):
    success: bool = Field(True, description="Deletion status")

    @classmethod
    def generate(self, request: DeleteRequest, public_key: str) -> "DeleteResponse":
        """
        """

        event_data = EventData.load(request.event_id)

        if event_data.data.owner_public_key != public_key:
            raise HTTPException(status_code=401, detail="Only an event owner may delete his own event")
        
        EventData.delete(request.event_id)

        return self(success=True)