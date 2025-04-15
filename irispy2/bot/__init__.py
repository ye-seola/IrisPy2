import json
import time
import typing as t

from loguru import logger
from websockets.sync.client import connect
from irispy2.bot._internal.emitter import EventEmitter
from irispy2.bot._internal.iris import IrisAPI, IrisRequest
from irispy2.bot.models import ChatContext, Message, Room, User


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

    def __process_chat(self, chat: ChatContext):
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

        room = Room(id=int(req.raw["chat_id"]), name=req.room)
        sender = User(id=int(req.raw["user_id"]), name=req.sender, api=self.api)
        msg = req.raw["message"]
        command, *params = msg.split(" ", 1)
        has_params = len(params) > 0
        message = Message(
            id=int(req.raw["id"]),
            type=int(req.raw["type"]),
            msg=req.raw["message"],
            attachment=req.raw["attachment"],
            v=v,
            command = command,
            has_params = has_params,
            params = params[0] if has_params else None,
        )

        chat = ChatContext(
            room=room, sender=sender, message=message, raw=req.raw, api=self.api
        )
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
