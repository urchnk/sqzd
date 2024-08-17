from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message


class AllowedUsersMiddleware(BaseMiddleware):
    def __init__(self, allowed_user_ids: list[int]):
        self.allowed_user_ids = allowed_user_ids

    async def __call__(
        self, handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]], event: Message, data: Dict[str, Any]
    ) -> Any:
        if str(event.from_user.id) in self.allowed_user_ids:
            return await handler(event, data)
