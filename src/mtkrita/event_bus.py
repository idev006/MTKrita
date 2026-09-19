from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable

from .messages import MessageEnvelope

MessageHandler = Callable[[MessageEnvelope], None]


class InProcessEventBus:
    """Simple synchronous MVP transport behind a stable message contract."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[MessageHandler]] = defaultdict(list)
        self._all_handlers: list[MessageHandler] = []

    def subscribe(self, message_type: str, handler: MessageHandler) -> Callable[[], None]:
        self._handlers[message_type].append(handler)

        def unsubscribe() -> None:
            handlers = self._handlers.get(message_type, [])
            if handler in handlers:
                handlers.remove(handler)

        return unsubscribe

    def subscribe_all(self, handler: MessageHandler) -> Callable[[], None]:
        self._all_handlers.append(handler)

        def unsubscribe() -> None:
            if handler in self._all_handlers:
                self._all_handlers.remove(handler)

        return unsubscribe

    def publish(self, message: MessageEnvelope) -> None:
        for handler in tuple(self._handlers.get(message.message_type, ())):
            handler(message)
        for handler in tuple(self._all_handlers):
            handler(message)
