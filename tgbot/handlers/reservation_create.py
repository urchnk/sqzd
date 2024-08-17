from datetime import datetime

from django.utils import timezone

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup

from bot import _
from tgbot.keyboards.default import get_client_main_menu, get_provider_services_keyboard, yes_no
from utils.bot.consts import DATE_FORMAT, TIME_FORMAT, weekdays
from utils.bot.to_async import get_available_hours, get_provider, get_service_data, get_user, set_reservation

reservation_create_router = Router()


class NewReservationStatesGroup(StatesGroup):
    service_selection = State()
    datetime_selection = State()


@reservation_create_router.message(NewReservationStatesGroup.service_selection)
async def service_selection(message: Message, state: FSMContext):
    if message.text == _("Yes"):
        state_data = await state.get_data()
        markup = await get_provider_services_keyboard(state_data["provider_id"])
        if len(markup.keyboard) > 1:
            await state.set_state(NewReservationStatesGroup.datetime_selection)
            await message.answer(_("Please, select a desirable service:"), reply_markup=markup)
        else:
            markup = await get_client_main_menu(message.from_user.id)
            await message.answer(
                _("This provider has no services listed at the moment."),
                reply_markup=markup,
            )
    elif message.text == _("No"):
        await state.clear()
        markup = await get_client_main_menu(message.from_user.id)
        await message.answer(_("You've canceled the booking process."), reply_markup=markup)
    else:
        markup = yes_no()
        await message.answer(_("Please, enter Yes or No."), reply_markup=markup)


@reservation_create_router.message(NewReservationStatesGroup.datetime_selection)
async def datetime_selection_or_complete_booking(message: Message, state: FSMContext):
    state_data = await state.get_data()
    if message.text == _("Next day"):
        service_name = state_data["service_name"]
        offset = state_data["offset"] + 1
        await state.update_data(offset=offset)
    elif message.text == _("Previous day"):
        service_name = state_data["service_name"]
        offset = state_data["offset"] - 1
        await state.update_data(offset=offset)
    elif message.text == _("Cancel booking"):
        await state.clear()
        await message.answer(
            _("You've canceled the booking process."),
            reply_markup=(await get_client_main_menu(message.from_user.id)),
        )
        return
    elif message.text.split(",")[0] in weekdays.values():
        state_data = await state.get_data()
        provider_id = int(state_data["provider_id"])
        provider_name = state_data["provider_name"]
        provider = await get_provider(provider_id)
        client = await get_user(tg_id=message.from_user.id)
        service_data = await get_service_data(state_data["service_name"], provider_id)
        weekday, strdate, strtime = message.text.split(", ")
        start_unaware = datetime.strptime((strdate + strtime), DATE_FORMAT + TIME_FORMAT)
        tz = timezone.get_current_timezone()
        start = timezone.make_aware(start_unaware, tz)
        await set_reservation(
            client=client,
            provider=provider,
            service_id=service_data["id"],
            start=start,
        )
        await state.clear()
        message_list = [
            _("You have booked the following reservation:\n"),
            state_data["service_name"],
            provider_name + ", @" + provider.user.tg_username,
            weekday + ", " + strdate + ", " + strtime,
        ]
        await message.answer(
            "\n".join(message_list),
            reply_markup=(await get_client_main_menu(tg_id=message.from_user.id)),
        )
        return
    else:
        service_name = message.text
        offset = 0
        await state.update_data(service_name=service_name, offset=offset)
    state_data = await state.get_data()
    provider_id = state_data["provider_id"]
    service_data = await get_service_data(service_name, int(provider_id))
    if not service_data:
        await state.clear()
        await message.answer(_("You've clearly entered something wrong. Please, try again."))
        return
    client_tg_id = message.from_user.id
    day, available_slots, is_day_off, is_vacation = await get_available_hours(
        tg_id=provider_id, client_tg_id=client_tg_id, service_name=service_name, offset=offset
    )
    date = weekdays[int(day.weekday())] + ", " + day.strftime(_("%m/%d/%Y"))  # TODO: handle date locales more nicely
    markup = ReplyKeyboardMarkup(keyboard=[[]], resize_keyboard=True, one_time_keyboard=True)
    for time in available_slots:
        time_string = time.strftime("%H:%M")
        button = KeyboardButton(text=f"{date}, {time_string}")
        markup.keyboard.append([button])
    if offset:
        row = [_("Previous day"), _("Today"), _("Next day")]
    else:
        row = [_("Next day")]
    markup.keyboard.append(row)
    markup.keyboard.append([_("Cancel booking")])
    await message.answer(
        _("Please, select the desirable date and time of the reservation."),
        reply_markup=markup,
    )
