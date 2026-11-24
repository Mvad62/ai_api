import asyncio
from collections import defaultdict


class ContextManager:
    """In-memory conversation history, isolated by Telegram user ID."""

    def __init__(self, max_messages: int) -> None:
        self._max_messages = max(2, max_messages - (max_messages % 2))
        self._contexts: dict[int, list[dict[str, str]]] = defaultdict(list)
        self._locks: dict[int, asyncio.Lock] = defaultdict(asyncio.Lock)

    def get_messages(self, user_id: int) -> list[dict[str, str]]:
        return list(self._contexts[user_id])

    def add_message(self, user_id: int, role: str, content: str) -> None:
        messages = self._contexts[user_id]
        messages.append({"role": role, "content": content})
        del messages[:-self._max_messages]

    def clear(self, user_id: int) -> None:
        self._contexts.pop(user_id, None)

    def lock_for(self, user_id: int) -> asyncio.Lock:
        return self._locks[user_id]
