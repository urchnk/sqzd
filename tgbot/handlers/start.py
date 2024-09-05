from aiogram import Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot import _
from tgbot.handlers.reservation_create import NewReservationStatesGroup
from tgbot.keyboards.inline import get_main_menu, yes_no
from utils.bot.services import get_client_reservations_as_message
from utils.bot.to_async import get_or_create_user, get_provider

start_router = Router()


@start_router.message(CommandStart(deep_link=True))
async def user_start_deeplink(message: Message, command: CommandObject(), state: FSMContext):
    await state.clear()
    last_name = message.from_user.last_name or None
    locale = "uk" if message.from_user.language_code in ["uk", "ru"] else "en"  # LOL, anyway TODO: de-hardcode this
    user = await get_or_create_user(
        tg_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=last_name,
        locale=locale,
    )
    await message.answer(_("Hello, ") + user.first_name)
    provider = await get_provider(username=command.args)
    provider_full_name = provider.user.get_full_name()
    provider_username = provider.user.username
    await state.set_state(NewReservationStatesGroup.service_selection)
    await state.update_data(provider_id=provider.user.tg_id, provider_name=provider_full_name)
    await message.answer(
        _("Do you want to book an reservation with provider {full_name} @{username}?").format(
            full_name=provider_full_name, username=provider_username
        ),
        reply_markup=yes_no(),
    )


@start_router.message(CommandStart(deep_link=False))
async def user_start(message: Message, state: FSMContext):
    await state.clear()
    last_name = message.from_user.last_name if message.from_user.last_name else None
    user = await get_or_create_user(
        tg_id=message.from_user.id,
        username=message.from_user.username,
        locale=message.from_user.language_code,
        first_name=message.from_user.first_name,
        last_name=last_name,
    )
    markup = await get_main_menu(message.from_user.id)
    reservations_as_message = await get_client_reservations_as_message(user.tg_id)
    await message.answer(
        _("Hello, ") + user.first_name + "\n" + reservations_as_message,
        reply_markup=markup,
    )
