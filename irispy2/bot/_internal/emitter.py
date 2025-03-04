import concurrent.futures
import typing as t
from loguru import logger
from irispy2.bot.models import ErrorContext


class EventEmitter:
    def __init__(self, max_workers=None):
        self.ev: dict[str, list[t.Callable]] = {}
        self.pool = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)

    def register(self, name: str, func: t.Callable):
        name = name.lower()

        if name not in self.ev:
            self.ev[name] = []

        self.ev[name].append(func)

    def emit(self, name: str, args: list[t.Any]):
        name = name.lower()

        for func in self.ev.get(name, []):
            self.pool.submit(self._handle_event, func, name, args)

    def _handle_event(self, func, name, args):
        try:
            func(*args)
        except Exception as e:
            if name == "error":
                logger.error(f"error handler에서 오류가 발생했습니다 ({e})")
                return

            self.emit(
                "error", [ErrorContext(event=name, func=func, exception=e, args=args)]
            )
