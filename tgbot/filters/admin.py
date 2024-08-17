from aiogram.filters import Filter
from aiogram.types import Message

from bot import config


class IsAdminFilter(Filter):

    async def __call__(self, message: Message):
        return message.from_user.id in config.tg_bot.admin_ids
