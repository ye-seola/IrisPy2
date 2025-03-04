import requests
from loguru import logger
import typing as t
import base64
from pydantic import BaseModel, Field


class IrisRequest(BaseModel):
    msg: str
    room: str
    sender: str
    raw: dict = Field(..., alias="json")


class IrisAPI:
    def __init__(self, iris_endpoint: str):
        self.iris_endpoint = iris_endpoint

    def __parse(self, res: requests.Response) -> dict:
        try:
            res: dict = res.json()
        except Exception:
            raise Exception(f"Iris 응답 JSON 파싱 오류: {res.text}")

        if res.get("success") is False:
            logger.debug(f"Iris 오류: {res}")
            raise Exception(f"Iris 오류: {res.get('error', '알 수 없는 오류')}")

        return res

    def reply(self, room_id: int, msg: str):
        res = requests.post(
            f"{self.iris_endpoint}/reply",
            json={"type": "text", "room": str(room_id), "data": str(msg)},
        )
        return self.__parse(res)

    def reply_media(
        self,
        room_id: int,
        type: t.Literal["IMAGE"],
        files: list[bytes],
    ):
        if type != "IMAGE":
            raise Exception("지원하지 않는 타입입니다")

        res = requests.post(
            f"{self.iris_endpoint}/reply",
            json={
                "type": "image_multiple",
                "room": str(room_id),
                "data": list(map(lambda v: base64.b64encode(v).decode(), files)),
            },
        )
        return self.__parse(res)

    def decrypt(self, enc: int, b64_ciphertext: str, user_id: int) -> str | None:
        res = requests.post(
            f"{self.iris_endpoint}/decrypt",
            json={"enc": enc, "b64_ciphertext": b64_ciphertext, "user_id": user_id},
        )

        res = self.__parse(res)
        return res.get("plain_text")

    def query(self, query: str, bind: list[t.Any] | None = None) -> list[dict]:
        res = requests.post(
            f"{self.iris_endpoint}/query", json={"query": query, "bind": bind or []}
        )
        res = self.__parse(res)
        return res.get("data", [])

    def get_info(self):
        res = requests.get(f"{self.iris_endpoint}/config/info")
        res = self.__parse(res)

        return res.get("message", {})
