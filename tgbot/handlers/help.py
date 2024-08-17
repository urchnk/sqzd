from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot import _

help_router = Router()


@help_router.message(Command(commands="help"))
async def bot_help(message: Message):
    text = [
        _("Commands: "),
        _("/start - Start the bot"),
        _("/register_provider = Register as a service provider"),
        _("/help - Get help"),
    ]
    await message.answer("\n".join(text))
