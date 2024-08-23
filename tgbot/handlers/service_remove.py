import datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardMarkup

from bot import _
from tgbot.filters.provider import IsProviderFilter
from tgbot.keyboards.default import get_provider_main_menu, yes_no
from utils.bot.to_async import (
    count_past_service_reservations,
    count_upcoming_service_reservations,
    get_provider_services,
    get_service_data,
    get_tz,
    is_provider,
    remove_service,
    update_service,
)

service_remove_router = Router()


class RemoveServiceStatesGroup(StatesGroup):
    choose_service = State()
    confirmation_deactivate = State()
    confirmation_remove = State()


@service_remove_router.message(F.text == _("Remove service"), IsProviderFilter())
async def list_services_for_removal(message: Message, state: FSMContext):
    if not await is_provider(message.from_user.id):
        await message.answer(_("You are not registered as a provider."))
    else:
        services = await get_provider_services(message.from_user.id)
        buttons = [[service.name] for service in services]
        buttons.append([_("Back to provider menu")])
        markup = ReplyKeyboardMarkup(keyboard=[[]], resize_keyboard=True, one_time_keyboard=True)
        for service in services:
            markup.keyboard.append([service.name])
        markup.keyboard.append([_("Back to provider menu")])
        await state.set_state(RemoveServiceStatesGroup.choose_service)
        await message.answer(_("Choose a service you want to remove:"), reply_markup=markup)


@service_remove_router.message(RemoveServiceStatesGroup.choose_service, IsProviderFilter())
async def choosing_service_to_remove(message: Message, state: FSMContext):
    service_data = await get_service_data(message.text, message.from_user.id)
    upcoming_reservations_count = await count_upcoming_service_reservations(
        service_id=service_data["id"],
        user_id=message.from_user.id,
    )
    past_reservations_count = await count_past_service_reservations(
        service_id=service_data["id"],
        user_id=message.from_user.id,
    )

    if upcoming_reservations_count or past_reservations_count:
        reply_message = _("This service has:\n")

        if upcoming_reservations_count:
            reply_message += _("Upcoming reservations: ") + f"{upcoming_reservations_count}\n"

        if past_reservations_count:
            reply_message += _("Past reservations: ") + f"{past_reservations_count}\n"

        reply_message += (
            _("You can only make it inactive now.\n")
            + _("Clients won't longer be able to book this service.\n")
            + _("Do you want to deactivate this service?")
        )
        await state.update_data(service_id=service_data["id"], service_name=service_data["name"])
        await state.set_state(RemoveServiceStatesGroup.confirmation_deactivate)
        await message.answer(reply_message, reply_markup=yes_no())
    else:
        reply_message = _("This service never had any reservations.\n") + _("Do you want to remove this service?")
        await state.update_data(service_id=service_data["id"], service_name=service_data["name"])
        await state.set_state(RemoveServiceStatesGroup.confirmation_remove)
        await message.answer(reply_message, reply_markup=yes_no())


@service_remove_router.message(RemoveServiceStatesGroup.confirmation_deactivate, IsProviderFilter())
async def confirmation_deactivate_service(message: Message, state: FSMContext):
    state_data = await state.get_data()
    service_id = state_data["service_id"]
    service_name = state_data["service_name"]
    markup = get_provider_main_menu()
    tz = await get_tz(message.from_user.id)
    if message.text == _("Yes"):
        await update_service(
            pk=service_id,
            name=_("{service_name} (deactivated {now})").format(
                service_name=service_name, now=datetime.datetime.now(tz=tz).strftime(_(""))
            ),
            is_active=False,
        )
        await state.clear()
        reply_message = _("Service {service_name} was successfully deactivated.").format(service_name=service_name)
        await message.answer(reply_message, reply_markup=markup)
    elif message.text == _("No"):
        await state.clear()
        await message.answer(
            _("You've canceled the service deactivation process."),
            reply_markup=markup,
        )
    else:
        await message.answer(_("Please, enter Yes or No."))


@service_remove_router.message(RemoveServiceStatesGroup.confirmation_remove, IsProviderFilter())
async def confirmation_remove_service(message: Message, state: FSMContext):
    state_data = await state.get_data()
    service_id = state_data["service_id"]
    service_name = state_data["service_name"]
    markup = get_provider_main_menu()
    if message.text == _("Yes"):
        await remove_service(pk=service_id)
        await state.clear()
        reply_message = _("Service {service_name} was successfully removed.").format(service_name=service_name)
        await message.answer(reply_message, reply_markup=markup)
    elif message.text == _("No"):
        await state.clear()
        await message.answer(_("You've canceled the service removal process."), reply_markup=markup)
    else:
        await message.answer(_("Please, enter Yes or No."))
