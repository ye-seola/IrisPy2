import json
import time
import typing as t

from loguru import logger
from websockets.sync.client import connect
from irispy2.bot.services import (
    ChannelService,
    DecryptService,
    MessageService,
    UserService,
)
from irispy2.core.emitter import EventEmitter
from irispy2.iris import IrisAPI, IrisRequest
from irispy2.bot.models import ChatEvent, Message, Channel, User


class Bot:
    def __init__(self, iris_url: str, *, max_workers=None):
        self.emitter = EventEmitter(max_workers=max_workers)

        self.iris_url = iris_url
        self.iris_ws_endpoint = (
            iris_url.replace(
                "http://",
                "ws://",
            ).replace(
                "https://",
                "wss://",
            )
            + "/ws"
        )

        self.api = IrisAPI(iris_url)

        my_user_id = self.api.get_info()["bot_id"]
        self.decrypt_service = DecryptService(my_user_id)
        self.user_service = UserService(self.api, self.decrypt_service)
        self.channel_service = ChannelService(self.api, self.user_service)
        self.message_service = MessageService(self.api, self.user_service)

    def __process_chat(self, chat: ChatEvent):
        self.emitter.emit("chat", [chat])

        origin = chat.message.v.get("origin")
        if origin == "MSG":
            self.emitter.emit("message", [chat])
        elif origin == "NEWMEM":
            self.emitter.emit("new_member", [chat])
        elif origin == "DELMEM":
            self.emitter.emit("del_member", [chat])

    def __process_iris_request(self, req: IrisRequest):
        v = {}
        try:
            v = json.loads(req.raw["v"])
        except Exception:
            pass

        attachment = {}
        try:
            attachment = json.loads(req.raw["attachment"])
        except Exception:
            pass

        channel = Channel(id=int(req.raw["chat_id"]))
        channel._name = req.room
        channel._channel_service = self.channel_service

        sender = User(id=int(req.raw["user_id"]))
        sender._name = req.sender
        sender._user_service = self.user_service

        message = Message(
            id=int(req.raw["id"]),
            type=int(req.raw["type"]),
            content=req.raw["message"],
            attachment=attachment,
            v=v,
            sender=sender,
        )
        message._message_service = self.message_service

        chat = ChatEvent(channel=channel, sender=sender, message=message, raw=req.raw)
        self.__process_chat(chat)

    def run(self):
        while True:
            try:
                with connect(self.iris_ws_endpoint, close_timeout=0) as ws:
                    logger.info("웹소켓에 연결되었습니다")
                    while True:
                        recv = ws.recv()
                        try:
                            data: dict = json.loads(recv)
                            data["raw"] = data.get("json")
                            del data["json"]

                            self.__process_iris_request(IrisRequest(**data))
                        except Exception as e:
                            logger.error(
                                "Iris 이벤트를 처리 중 오류가 발생했습니다: {}", e
                            )
            except Exception as e:
                logger.error("웹소켓 연결 오류: {}", e)
                logger.error("3초 후 재연결합니다")

            time.sleep(3)

    def on_event(self, name: str):
        def decorator(func: t.Callable):
            self.emitter.register(name, func)

            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper

        return decorator
