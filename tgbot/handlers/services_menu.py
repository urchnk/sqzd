from aiogram import F, Router
from aiogram.types import Message

from bot import _
from tgbot.filters.provider import IsProviderFilter
from tgbot.keyboards.default import get_provider_services_menu
from utils.bot.services import get_provider_services_as_message

services_menu_router = Router()


@services_menu_router.message(F.text == _("Services menu"), IsProviderFilter())
async def show_services_menu(message: Message):
    markup = get_provider_services_menu()
    reply_message = await get_provider_services_as_message(message.from_user.id)
    if reply_message:
        await message.answer(reply_message, reply_markup=markup)
    else:
        await message.answer(_("You have no services set up at the moment."), reply_markup=markup)
