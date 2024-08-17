from aiogram.filters import Filter
from aiogram.types import Message


class IsProviderFilter(Filter):
    async def __call__(self, message: Message) -> bool:
        from utils.bot.to_async import is_provider

        return await is_provider(message.from_user.id)
