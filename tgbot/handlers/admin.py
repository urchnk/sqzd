from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from tgbot.filters.admin import IsAdminFilter

admin_router = Router(name="admin")


@admin_router.message(IsAdminFilter())
async def debug(message: Message):
    pass
