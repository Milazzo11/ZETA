from pydantic import BaseModel, Field
from fastapi import HTTPException


class Error(BaseModel):
    error: bool = Field(True, description="Error status")
    detail: str = Field(..., description="Error detail")

    @classmethod
    def generate(self, exception: HTTPException) -> "Error":
        """
        """

        detail = exception.detail

        return self(error=True, detail=detail)
    

    def to_dict(self) -> dict:
        return self.__dict__