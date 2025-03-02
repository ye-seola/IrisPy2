from irispy2.bot import Bot
from loguru import logger

from irispy2.bot.models import ChatContext
from irispy2.compat.pykakaodb import KakaoDB, Replier
from irispy2.compat.pykakaodb import context
import typing as t


class LegacyBot(Bot):
    def __init__(self, iris_endpoint, bot_id: int = None, bot_name: str = None):
        super().__init__(iris_endpoint)

        self.__state = {}

        self.__bot_id = bot_id
        self.__bot_name = bot_name

        if bot_name is None or bot_id is None:
            logger.info("bot_name 또는 bot_id가 주어지지 않아 Iris에서 불러옵니다.")
            self.__load_config()

        self._ctx = context.PyKakaoDBContext(self.__bot_id, self.__bot_name, self.api)
        context.set_context(self._ctx)

        self.__kakaodb = KakaoDB(self._ctx)

    def __load_config(self):
        try:
            self.__info = self.api.get_info()
        except Exception as e:
            logger.error(f"Iris에서 정보를 불러오지 못했습니다: {e}")
            exit(1)

        if "bot_id" not in self.__info:
            raise Exception("bot_id이 Iris 설정에 존재하지 않습니다")

        if "bot_name" not in self.__info:
            raise Exception("bot_name이 Iris 설정에 존재하지 않습니다")

        self.__bot_id = self.__info["bot_id"]
        self.__bot_name = self.__info["bot_name"]

        logger.info(f"bot_id: {self.__bot_id}, bot_name: {self.__bot_name}")

    def response(self, func: t.Callable):
        def response_wrapper(chat: ChatContext):
            replier = Replier(chat, self.api)
            func(
                chat.room.name,
                chat.message.msg,
                chat.sender.name,
                replier,
                chat.raw,
                self.__kakaodb,
                self.__state,
            )

        self.emitter.register("chat", response_wrapper)

        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper
