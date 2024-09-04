from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

import requests
from bot import IPGEOLOCATION_API_KEY
from tgbot.filters.admin import IsAdminFilter

admin_router = Router(name="admin")


@admin_router.message()
async def debug(message: Message):
    print(message.text)
    pass
