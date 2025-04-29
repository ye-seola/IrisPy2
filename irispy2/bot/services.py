import json
import traceback
import typing as t

from loguru import logger

from irispy2.core.decrypt import decrypt as kakaotalk_decrypt
from irispy2.iris import IrisAPI

MediaType = t.Union[
    t.Literal["IMAGE"],
    t.Literal["FILE"],
    t.Literal["AUDIO"],
    t.Literal["VIDEO"],
]


class DecryptService:
    def __init__(self, user_id: int):
        self.user_id = user_id

    def decrypt(self, enc_type: int, b64_ciphertext: str, user_id: int = None):
        if user_id is None:
            user_id = self.user_id

        try:
            return kakaotalk_decrypt(user_id, enc_type, b64_ciphertext)
        except Exception:
            return b64_ciphertext


class MessageService:
    def __init__(self, api: IrisAPI, user_service: "UserService"):
        self._api = api
        self._user_service = user_service

    def get_message_from_log_id(self, log_id: str):
        from irispy2.bot.models import Message, User

        rows = self._api.query("SELECT * FROM chat_logs WHERE id = ?", [log_id])
        if rows:
            row = rows[0]

            attachment = {}
            try:
                attachment = json.loads(row["attachment"])
            except Exception:
                pass

            v = {}
            try:
                v = json.loads(row["v"])
            except Exception:
                pass

            sender = sender = User(id=int(row["user_id"]))
            sender._user_service = self._user_service

            return Message(
                row["id"], row["type"], row["message"], attachment, v, sender
            )


class ChannelService:
    def __init__(self, api: IrisAPI, user_service: "UserService"):
        self._api = api
        self._user_service = user_service

    def send(self, channel_id: int, message: str):
        try:
            self._api.reply(channel_id, message)
            return True
        except Exception as e:
            logger.error(f"reply 오류: {e}")
            return False

    def send_media(
        self,
        channel_id: int,
        media_type: MediaType,
        media: bytes | t.List[bytes],
    ):
        if media_type != "IMAGE":
            raise Exception("지원하지 않는 타입입니다")

        if isinstance(media, bytes):
            media = [media]

        try:
            self._api.reply_media(channel_id, media_type, media)

            return True
        except Exception as e:
            traceback.print_exc()
            logger.error(f"reply_media 오류: {e}")

            return False

    def get_type(self, channel_id: int) -> t.Optional[str]:
        row = self._api.query(
            "SELECT type, meta FROM chat_rooms WHERE id = ?",
            [channel_id],
        )
        if row:
            type = row[0]["type"]
            meta = row[0]["meta"]

            if type == "MultiChat" and "warehouse" in meta:
                return "TeamChat"

            return type

    def get_name(self, channel_id: int, picker=False) -> t.Optional[str]:
        type = self.get_type(channel_id)

        if type == "OM":
            row = self._api.query(
                "SELECT name FROM db2.open_link WHERE id = (SELECT link_id FROM chat_rooms WHERE id = ?)",
                [channel_id],
            )
            return row[0]["name"]

        elif type == "TeamChat":
            row = self._api.query(
                "SELECT name FROM warehouse_info WHERE chat_id = ?",
                [channel_id],
            )
            return row[0]["name"]

        elif type == "MultiChat":
            row = self._api.query(
                "SELECT v FROM chat_rooms WHERE id = ?",
                [channel_id],
            )
            if row:
                try:
                    v = json.loads(row[0]["v"])

                    display_user_ids: str = v["display_user_ids"]
                    display_user_id_list = [
                        *map(str.strip, display_user_ids.split(","))
                    ]

                    name_map = self._user_service.get_bulk_name(display_user_id_list)
                    name = map(
                        lambda id: name_map.get(id, "(알 수 없음)"),
                        display_user_id_list,
                    )

                    if picker:
                        return ",".join(name)
                    else:
                        return ", ".join(name)
                except Exception:
                    pass

    def get_custom_name(self, channel_id: int) -> t.Optional[str]:
        row = self._api.query(
            "SELECT private_meta FROM chat_rooms WHERE id = ?", [channel_id]
        )
        if row:
            try:
                private_meta: dict = json.loads(row[0]["private_meta"])
                return private_meta.get("name")
            except Exception:
                pass


class UserService:
    def __init__(self, api: IrisAPI, decrypt: DecryptService):
        self._api = api
        self._decrypt = decrypt

    def get_profile_url(self):
        row = self._api.query(
            "SELECT original_profile_image_url, enc FROM db2.friends WHERE id = ?"
        )
        if row:
            return self._decrypt.decrypt(row["original_profile_image_url"], row["name"])

        row = self._api.query(
            "SELECT original_profile_image_url, env FROM db2.open_chat_member WHERE id = ?"
        )
        if row:
            return self._decrypt.decrypt(row["enc"], row["original_profile_image_url"])

        return None

    def get_name(self, user_id: int) -> str:
        rows = self._api.query(
            "SELECT name, enc FROM db2.friends WHERE id = ?", [user_id]
        )
        if rows:
            row = rows[0]
            return self._decrypt.decrypt(row["enc"], row["name"])

        rows = self._api.query(
            "SELECT nickname as name, enc FROM db2.open_chat_member WHERE user_id = ?",
            [user_id],
        )
        if rows:
            row = rows[0]
            return self._decrypt.decrypt(row["enc"], row["name"])

        return None

    def get_bulk_name(self, user_ids: list[int]) -> dict[str, str]:
        if not user_ids:
            return {}

        name_map = {}

        placeholders = ",".join("?" for _ in user_ids)
        for row in self._api.query(
            f"SELECT id, name, enc FROM db2.friends WHERE id IN ({placeholders})",
            user_ids,
        ):
            name_map[row["id"]] = self._decrypt.decrypt(row["enc"], row["name"])

        missing_ids = [uid for uid in user_ids if uid not in name_map]
        if missing_ids:
            placeholders = ",".join("?" for _ in missing_ids)
            for row in self._api.query(
                f"SELECT id, nickname as name, enc FROM db2.open_chat_member WHERE id IN ({placeholders})",
                missing_ids,
            ):
                name_map[row["id"]] = self._decrypt.decrypt(row["enc"], row["name"])

        return name_map

    def get_link_id(self, user_id: int) -> str:
        row = self._api.query(
            "SELECT link_id FROM db2.open_chat_member WHERE id = ?", [user_id]
        )
        if row:
            return row[0].get("link_id", None)

        return None
