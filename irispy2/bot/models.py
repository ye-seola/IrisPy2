from dataclasses import dataclass
import typing as t
from irispy2.bot._internal.iris import IrisAPI
from loguru import logger


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

    def reply(self, message: str, room_id=None):
        if room_id is None:
            room_id = self.room.id

        try:
            self.__api.reply(room_id, message)
        except Exception as e:
            logger.error(f"reply 오류: {e}")

    def reply_media(
        self,
        type: t.Literal["IMAGE"],
        files: list[t.IO[bytes]],
        room_id=None,
    ):
        if room_id is None:
            room_id = self.room.id

        if type != "IMAGE":
            raise Exception("지원하지 않는 타입입니다")

        try:
            files: list[bytes] = list(map(lambda v: v.read(), files))
            self.__api.reply_media(room_id, type, files)
        except Exception as e:
            logger.error(f"reply_media 오류: {e}")


@dataclass
class ErrorContext:
    event: str
    func: t.Callable
    exception: Exception
    args: list[t.Any]
