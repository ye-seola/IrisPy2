import io
import os
import typing
from PIL import Image

from irispy2.bot._internal.iris import IrisAPI
from irispy2.bot.models import ChatContext


class Replier:
    def __init__(self, chat: ChatContext, api: IrisAPI):
        self.__chat = chat
        self.__api = api

    def reply(self, msg: str, room_id: str = None):
        if room_id is None:
            room_id = self.__chat.room.id

        self.__api.reply(room_id, msg)

    def reply_image_from_file(
        self, room: str, fp: str | os.PathLike | typing.IO[bytes]
    ):
        img = Image.open(fp)
        self.reply_image_from_image(room, img)

    def reply_image_from_image(self, room_id: str, img: Image.Image):
        if room_id is None:
            room_id = self.__chat.room.id

        bio = io.BytesIO()
        img.save(bio, format="PNG")

        self.__api.reply_media(room_id, "IMAGE", [bio.getvalue()])
