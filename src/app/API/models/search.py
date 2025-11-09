"""
/search endpoint data packet models.

:author: Max Milazzo
"""



from app.data.event import Event

from pydantic import BaseModel, Field
from typing import List, Literal, Self



class SearchRequest(BaseModel):
    """
    /search user request.
    """
    
    text: str = Field(..., description="Search text pattern to find relevant events")
    limit: int = Field(16, ge=1, le=64, description="Maximum number of results")
    mode: Literal["id", "text"] = Field("id", description="Search mode")



class SearchResponse(BaseModel):
    """
    /search server response.
    """

    events: List[Event] = Field(..., description="List of found events")


    @classmethod
    def generate(cls, request: SearchRequest) -> Self:
        """
        Generate the server response from a user request.

        :param request: user request
        :return: server response
        """

        if request.mode.lower() == "id":
            events = [Event.load(request.text)]

        else:
            events = Event.search(request.text, request.limit)

        return cls(events=events)