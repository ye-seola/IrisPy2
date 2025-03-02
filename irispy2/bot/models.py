from dataclasses import dataclass
from irispy2.bot._internal import IrisAPI


@dataclass
class Message:
    id: int
    type: int
    msg: str
    attachment: str
    v: dict


@dataclass
class Room:
    id: int
    name: str


@dataclass
class User:
    id: int
    name: str


@dataclass(init=False)
class ChatContext:
    room: Room
    sender: User
    message: Message
    raw: dict

    def __init__(
        self, room: Room, sender: User, message: Message, raw: dict, api: IrisAPI
    ):
        self.__api = api
        self.room = room
        self.sender = sender
        self.message = message
        self.raw = raw

    def reply(self, message: str):
        self.__api.reply(self.room.id, message)
