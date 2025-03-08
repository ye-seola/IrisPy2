import contextvars
from dataclasses import dataclass
import typing as t
from irispy2.bot._internal.iris import IrisAPI
from loguru import logger


@dataclass
class PyKakaoDBContext:
    bot_id: int
    bot_name: str
    api: IrisAPI


_store: contextvars.ContextVar[PyKakaoDBContext] = contextvars.ContextVar(
    "irispy2.compat.pykakaodb._ontext"
)


def set_context(ctx: PyKakaoDBContext):
    return _store.set(ctx)


def get_context():
    ctx = _store.get(None)
    if ctx is None:
        err = "컨텍스트를 찾을 수 없습니다. 스레드를 실행하셨다면 irispy2.compat.pykakaodb.context.copy_context를 사용해주세요"
        logger.error(err)
        raise Exception(err)

    return ctx


def copy_context(func: t.Callable):
    ctx = contextvars.copy_context()

    def wrapper(*args, **kwargs):
        ctx.run(lambda: func(*args, **kwargs))

    return wrapper
