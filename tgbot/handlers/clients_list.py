from aiogram import F, Router
from aiogram.types import Message

from bot import _
from tgbot.filters.provider import IsProviderFilter
from tgbot.keyboards.default import get_provider_main_menu
from utils.bot.services import get_provider_clients_as_message

clients_list_router = Router(name="clients_list")


@clients_list_router.message(F.text == _("Clients"), IsProviderFilter())
async def list_clients(message: Message):
    markup = get_provider_main_menu()
    reply_message = await get_provider_clients_as_message(message.from_user.id)
    await message.answer(text=reply_message, reply_markup=markup)
