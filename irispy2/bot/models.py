from dataclasses import dataclass
import io
import traceback
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
        mediaType: t.Literal["IMAGE"],
        files: list[t.IO[bytes] | bytes],
        room_id=None,
    ):
        if room_id is None:
            room_id = self.room.id

        if mediaType != "IMAGE":
            raise Exception("지원하지 않는 타입입니다")

        def convert(e: t.IO[bytes] | bytes):
            if isinstance(e, io.BufferedIOBase):
                return e.read()
            elif isinstance(e, bytes):
                return e
            else:
                raise Exception(f"알 수 없는 타입입니다 {type(e)}")

        try:
            files: list[bytes] = list(map(convert, files))
            self.__api.reply_media(room_id, mediaType, files)
        except Exception as e:
            traceback.print_exc()
            logger.error(f"reply_media 오류: {e}")


@dataclass
class ErrorContext:
    event: str
    func: t.Callable
    exception: Exception
    args: list[t.Any]
