from aiogram.filters import Filter
from aiogram.types import Message

from bot import ADMINS


class IsAdminFilter(Filter):

    async def __call__(self, message: Message):
        return message.from_user.id in ADMINS
