from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from bot import _
from tgbot.filters.provider import IsProviderFilter
from tgbot.keyboards.default import get_client_main_menu, get_provider_main_menu
from utils.bot.services import get_client_reservations_as_message
from utils.bot.to_async import is_provider

menu_router = Router(name="menu")


async def get_main_menu(tg_id: int):
    if await is_provider(tg_id):
        return get_provider_main_menu()
    else:
        return await get_client_main_menu(tg_id)


@menu_router.message(
    F.text.in_([_("Main menu"), _("My provider menu"), _("Back to main menu"), _("Back to provider menu"), _("Cancel")])
)
async def show_provider_menu(message: Message):
    await message.answer(text=_("Main menu:"), reply_markup=await get_main_menu(message.from_user.id))


@menu_router.message(F.text.in_([_("Main menu"), _("My client menu"), _("Back to main menu"), _("Cancel")]))
async def show_client_menu(message: Message):
    answer_message = _("Client menu:") if await is_provider(message.from_user.id) else _("Main menu:")
    await message.answer(text=answer_message, reply_markup=await get_client_main_menu(message.from_user.id))


@menu_router.message(F.text.in_([_("Upcoming reservations"), _("Past reservations")]))
async def get_upcoming_reservations(message: Message):
    is_past = True if (message.text == _("Past reservations")) else False
    markup = await get_client_main_menu(message.from_user.id)
    reply_message = await get_client_reservations_as_message(message.from_user.id, is_past=is_past)
    return await message.answer(text=reply_message, reply_markup=markup)
