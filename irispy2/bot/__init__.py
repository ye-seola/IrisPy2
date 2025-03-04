import json
import typing as t

import uvicorn
from fastapi import BackgroundTasks, FastAPI
from irispy2.bot._internal.emitter import EventEmitter
from irispy2.bot._internal.iris import IrisAPI, IrisRequest
from irispy2.bot.models import ChatContext, Message, Room, User


class Bot:
    def __init__(self, iris_endpoint: str, *, max_workers=None):
        self.emitter = EventEmitter(max_workers=max_workers)

        self.api = IrisAPI(iris_endpoint)

        self.fastapi = FastAPI()
        self.fastapi.add_api_route(
            path="/db", endpoint=self.__on_iris_request, methods=["POST"]
        )

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
        sender = User(id=int(req.raw["user_id"]), name=req.sender)
        message = Message(
            id=int(req.raw["id"]),
            type=int(req.raw["type"]),
            msg=req.raw["message"],
            attachment=req.raw["attachment"],
            v=v,
        )

        chat = ChatContext(
            room=room, sender=sender, message=message, raw=req.raw, api=self.api
        )
        self.__process_chat(chat)

    def __on_iris_request(self, req: IrisRequest, background_tasks: BackgroundTasks):
        background_tasks.add_task(self.__process_iris_request, req)
        return {}

    def run(self, port: int, host="0.0.0.0"):
        uvicorn.run(
            app=self.fastapi,
            host=host,
            port=port,
        )

    def on_event(self, name: str):
        def decorator(func: t.Callable):
            self.emitter.register(name, func)

            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper

        return decorator
