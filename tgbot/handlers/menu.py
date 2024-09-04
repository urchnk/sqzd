from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot import _
from tgbot.filters.provider import IsProviderFilter
from tgbot.keyboards.inline import get_client_main_menu, get_main_menu, get_provider_main_menu
from utils.bot.services import get_client_reservations_as_message
from utils.bot.to_async import is_provider

menu_router = Router(name="menu")


@menu_router.callback_query(
    F.data.in_(
        [
            "provider_menu",
            "main_menu",
        ]
    ),
    IsProviderFilter(),
)
async def show_provider_menu(query: CallbackQuery):
    await query.answer()
    if await is_provider(query.from_user.id):
        await query.message.edit_text(_("Main menu:"), reply_markup=get_provider_main_menu())
    else:
        markup = await get_main_menu(query.from_user.id)
        await query.message.edit_text(_("Main menu:"), reply_markup=markup)


@menu_router.callback_query(
    F.data.in_(
        [
            "client_menu",
            "main_menu",
        ]
    ),
)
async def show_client_menu(query: CallbackQuery):
    await query.answer()
    markup = await get_client_main_menu(query.from_user.id)
    answer_message = _("Client menu:") if await is_provider(query.from_user.id) else _("Main menu:")
    await query.message.edit_text(answer_message, reply_markup=markup)


@menu_router.callback_query(F.data.in_(["upcoming_reservations", "past_reservations"]))
async def get_upcoming_reservations(query: CallbackQuery):
    await query.answer()
    is_past = True if (query.data == "past_reservations") else False
    markup = await get_client_main_menu(query.from_user.id)
    reply_message = await get_client_reservations_as_message(query.from_user.id, is_past=is_past)
    return await query.message.edit_text(reply_message, reply_markup=markup)
