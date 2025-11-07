"""
/search endpoint data packet models.

:author: Max Milazzo
"""



from app.data.event import Event

from pydantic import BaseModel, Field
from typing import List, Self



class SearchRequest(BaseModel):
    """
    /search user request.
    """
    
    text: str = Field(..., description="The search text or keywords to find relevant events")
    limit: int = Field(1, description="The maximum number of results to return")
    mode: str = Field("id", description='Search mode: "id" or "text"')



class SearchResponse(BaseModel):
    """
    /search server response.
    """

    events: List[Event] = Field(..., description="List of events matching search parameters")


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