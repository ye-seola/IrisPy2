import time
from loguru import logger
from irispy2.compat.pykakaodb import context


class KakaoDB:
    def __init__(self, ctx: context.PyKakaoDBContext = None):
        if ctx is None:
            ctx = context.get_context()
            self.__ctx = ctx
        else:
            self.__ctx = ctx

    def __query(self, query, bind=None, err_raise=False) -> list[dict]:
        try:
            return self.__ctx.api.query(query, bind)
        except Exception as e:
            logger.error(f"쿼리 오류: {e}")

            if err_raise:
                raise

            return []

    def get_column_info(self, table):
        rows = self.__query(f"SELECT * FROM {table} LIMIT 1")
        if not rows:
            return []

        return list(rows[0].keys())

    def get_table_info(self):
        rows = self.__query("SELECT name FROM sqlite_master WHERE type='table'")
        if not rows:
            return []

        return [row["name"] for row in rows]

    def get_name_of_user_id(self, user_id) -> str | None:
        if user_id == self.__ctx.bot_id:
            return self.__ctx.bot_name

        if not self.check_new_db():
            query = "SELECT name, enc FROM db2.friends WHERE id = ?"
        else:
            query = """
                    WITH info AS (
                        SELECT ? AS user_id
                    )
                    SELECT
                        COALESCE(open_chat_member.nickname, friends.name) AS name,
                        COALESCE(open_chat_member.enc, friends.enc) AS enc
                    FROM info
                    LEFT JOIN db2.open_chat_member
                        ON open_chat_member.user_id = info.user_id
                    LEFT JOIN db2.friends
                        ON friends.id = info.user_id;
                    """

        rows = self.__query(query, bind=[user_id])
        if not rows:
            return None

        row = rows[0]
        return self.decrypt(row["enc"], row["name"])

    def get_user_info(self, chat_id, user_id):
        sender = self.get_name_of_user_id(user_id)

        rows = self.__query(
            "SELECT name FROM db2.open_link WHERE id = (SELECT link_id FROM chat_rooms WHERE id = ?)",
            bind=[chat_id],
        )

        if not rows:
            room = sender
        else:
            room = rows[0]["name"]

        return (room, sender)

    def get_row_from_log_id(self, log_id: str | int):
        rows = self.__query("SELECT * FROM chat_logs WHERE id = ?", bind=[log_id])
        if not rows:
            return None

        return list(rows[0].values())

    def clean_chat_logs(self, days: str | int | float):
        try:
            days = float(days)
            days_before_now = round(time.time() - days * 24 * 60 * 60)
            self.__query(
                "delete from chat_logs where created_at < ?",
                bind=[days_before_now],
                err_raise=True,
            )
            res = f"{days:g}일 이상 지난 데이터가 삭제되었습니다."
        except Exception:
            res = "요청이 잘못되었거나 에러가 발생하였습니다."
        return res

    def log_to_dict(self, log_id) -> dict:
        rows = self.__query("select * from chat_logs where id = ?", bind=[log_id])
        if not rows:
            return {}

        return rows[0]

    def check_new_db(self):
        data = self.__query(
            "SELECT name FROM db2.sqlite_master WHERE type='table' AND name='open_chat_member'"
        )
        if not data:
            return False

        return True

    def decrypt(self, encType: int, b64_ciphertext: str, user_id: int = None):
        if user_id is None:
            user_id = self.__ctx.bot_id

        try:
            return self.__ctx.api.decrypt(encType, b64_ciphertext, user_id)
        except Exception as e:
            logger.error(f"Iris 복호화 오류: {e}")
            return None
