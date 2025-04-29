from dataclasses import dataclass, field
from enum import Enum
from functools import cached_property
import typing as t

from irispy2.bot.services import MessageService, ChannelService, UserService, MediaType


class MessageType(Enum):
    FEED = 0
    TEXT = 1
    PHOTO = 2
    VIDEO = 3
    CONTACT = 4
    AUDIO = 5
    ANIMATED_EMOTICON = 6
    DIGITAL_ITEM_GIFT = 7
    LINK = 9
    OLD_LOCATION = 10
    AVATAR = 11
    STICKER = 12
    SCHEDULE = 13
    VOTE = 14
    LOCATION = 16
    PROFILE = 17
    FILE = 18
    ANIMATED_STICKER = 20
    NUDGE = 21
    SPRITECON = 22
    SHARP_SEARCH = 23
    POST = 24
    ANIMATED_STICKER_EX = 25
    REPLY = 26
    MULTI_PHOTO = 27
    MVOIP = 51
    VOX_ROOM = 52
    LEVERAGE = 71
    ALIMTALK = 72
    PLUS_LEVERAGE = 73
    PLUS = 81
    PLUS_EVENT = 82
    PLUS_VIRAL = 83
    SCHEDULE_FOR_OPEN_LINK = 96
    VOTE_FOR_OPEN_LINK = 97
    POST_FOR_OPEN_LINK = 98


@dataclass
class Message:
    _message_service: MessageService = field(init=False, default=None)

    id: int
    type: int
    content: str
    attachment: dict
    v: dict
    sender: "User"

    @cached_property
    def source(self) -> t.Optional["Message"]:
        if self.type != MessageType.REPLY.value:
            return None

        log_id = self.attachment.get("src_logId")
        if log_id:
            return self._message_service.get_message_from_log_id(log_id)


@dataclass
class Channel:
    _name: str = field(init=False, default=None)
    _channel_service: ChannelService = field(init=False, default=None)

    id: int

    @cached_property
    def name(self):
        if self._name is not None:
            return self._name

        custom_name = self._channel_service.get_custom_name(self.id)
        if custom_name:
            return custom_name

        return self._channel_service.get_name(self.id)

    @cached_property
    def original_name(self):
        return self._channel_service.get_name(self.id)

    def send(self, message: str):
        return self._channel_service.send(self.id, message)

    def send_media(
        self,
        media_type: MediaType,
        media: bytes | t.List[bytes],
    ):
        return self._channel_service.send_media(self.id, media_type, media)


@dataclass
class User:
    _name: str = field(init=False, default=None)
    _user_service: UserService = field(init=False, default=None)

    id: int

    @cached_property
    def name(self) -> t.Optional[str]:
        if self._name is not None:
            return self._name

        return self._user_service.get_name(self.id)

    @cached_property
    def link_id(self) -> t.Optional[str]:
        return self._user_service.get_link_id(self.id)

    @cached_property
    def profile_url(self) -> t.Optional[str]:
        return self._user_service.get_profile_url(self.id)


@dataclass()
class ChatEvent:
    channel: Channel
    sender: User
    message: Message
    raw: dict
