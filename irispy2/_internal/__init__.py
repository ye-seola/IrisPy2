from dataclasses import dataclass

from pydantic import BaseModel, Field


@dataclass
class ReplyQueueItem:
    room_id: int
    msg: str


@dataclass
class ReplyMediaQueueItem:
    room_id: int
    type: str
    files: tuple[bytes]


class IrisRequest(BaseModel):
    msg: str
    room: str
    sender: str
    meta: dict = Field(..., alias="json")
