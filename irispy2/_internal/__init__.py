from pydantic import BaseModel, Field


class IrisRequest(BaseModel):
    msg: str
    room: str
    sender: str
    meta: dict = Field(..., alias="json")
