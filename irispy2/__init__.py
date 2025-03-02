__version__ = "0.0.0"
__version_tuple__ = (0, 0, 0)

from contextvars import ContextVar
from dataclasses import dataclass

from fastapi import BackgroundTasks, FastAPI
import requests
import uvicorn

from irispy2.models import Room, User, Message
from irispy2._internal import IrisRequest


@dataclass
class AppContext:
    room: Room
    sender: User
    message: Message


_store: ContextVar[AppContext] = ContextVar("IrisPy2.Context")


class IrisAPI:
    def __init__(self, iris_endpoint: str):
        self.iris_endpoint = iris_endpoint

    def reply(self, room_id: int, msg: str):
        requests.post(
            f"{self.iris_endpoint}/reply",
            json={"type": "text", "room": str(room_id), "data": str(msg)},
        )


class IrisPy:
    def __init__(self):
        self.__app = FastAPI()
        self.__app.add_api_route(
            path="/iris", endpoint=self.__on_iris_request, methods=["POST"]
        )
        self.__app.add_event_handler("shutdown", self.__on_fastapi_shutdown)
        self.__api: IrisAPI = None

    def on_message(self, room: Room, sender: User, message: Message):
        pass

    def reply(self, msg: str, room_id: int = None):
        if room_id is None:
            ctx = _store.get(None)

            if ctx is None:
                raise Exception("컨텍스트가 존재하지 않습니다")

            room_id = ctx.room.id

        self.__api.reply(room_id, msg)

    def reply_media(self, type: str, files: list[bytes], room_id: int = None):
        if room_id is None:
            ctx = _store.get(None)

            if ctx is None:
                raise Exception("컨텍스트가 존재하지 않습니다")

            room_id = ctx.room.id
        
        # TODO: impl

    def run(self, *, port: int, iris_endpoint: str):
        self.__api = IrisAPI(iris_endpoint)

        uvicorn.run(
            app=self.__app,
            host="0.0.0.0",
            port=port,
        )

    def __process_iris_request(self, req: IrisRequest):
        room = Room(id=int(req.meta["chat_id"]), name=req.room)
        sender = User(id=int(req.meta["user_id"]), name=req.sender)
        message = Message(
            id=int(req.meta["id"]),
            type=int(req.meta["type"]),
            msg=req.meta["message"],
            attachment=req.meta["attachment"],
            v=req.meta["v"],
        )

        _store.set(AppContext(room=room, sender=sender, message=message))
        self.on_message(room=room, sender=sender, message=message)

    def __on_iris_request(self, req: IrisRequest, background_tasks: BackgroundTasks):
        background_tasks.add_task(self.__process_iris_request, req)
        return {}

    def __on_fastapi_shutdown(self):
        pass
