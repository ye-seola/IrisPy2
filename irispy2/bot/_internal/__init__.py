from pydantic import BaseModel, Field
import requests
import typing as t


class IrisRequest(BaseModel):
    msg: str
    room: str
    sender: str
    meta: dict = Field(..., alias="json")


class IrisAPI:
    def __init__(self, iris_endpoint: str):
        self.iris_endpoint = iris_endpoint

    def reply(self, room_id: int, msg: str):
        requests.post(
            f"{self.iris_endpoint}/reply",
            json={"type": "text", "room": str(room_id), "data": str(msg)},
        )


class EventEmitter:
    def __init__(self):
        self.ev: dict[str, list[t.Callable]] = {}

    def register(self, name: str, func: t.Callable):
        name = name.lower()

        if name not in self.ev:
            self.ev[name] = []

        self.ev[name].append(func)

    def emit(self, name: str, args: list[t.Any]):
        name = name.lower()

        for func in self.ev.get(name, []):
            func(*args)
