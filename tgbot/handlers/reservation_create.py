import datetime
import itertools

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup

from bot import _, bot
from tgbot.keyboards.default import get_client_main_menu, get_provider_services_keyboard, yes_no
from utils.bot.consts import DATE_FORMAT, TIME_FORMAT, WDS, WEEKDAYS
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
    provider_id = int(state_data["provider_id"])
    provider = await get_provider(provider_id)

    if message.text == _("Next day"):
        service_name = state_data["service_name"]
        offset = state_data["offset"] + 1
        await state.update_data(offset=offset)

    elif message.text == _("Today"):
        service_name = state_data["service_name"]
        offset = 0
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

    elif len(message.text) == 5 and (":" in message.text):
        state_data = await state.get_data()
        provider_name = state_data["provider_name"]
        client = await get_user(tg_id=message.from_user.id)
        service_data = await get_service_data(state_data["service_name"], provider_id)
        hour = int(message.text.split(":")[0])
        minute = int(message.text.split(":")[1])
        date: datetime.date = state_data["date"]
        tz = client.tz
        start = datetime.datetime.combine(date, datetime.time(hour=hour, minute=minute), tzinfo=tz)

        await set_reservation(
            client=client,
            provider=provider,
            service_id=service_data["id"],
            start=start,
        )
        await state.clear()
        message_list = [
            _("You have booked the following reservation:\n"),
            state_data["service_name"]
            + ", "
            + str(service_data["price"].amount)
            + " "
            + str(service_data["price"].currency),
            provider_name + ", @" + provider.user.tg_username,
            _(WDS[date.weekday()]) + ", " + start.strftime(DATE_FORMAT) + ", " + start.strftime(TIME_FORMAT),
        ]
        await message.answer(
            "\n".join(message_list),
            reply_markup=(await get_client_main_menu(tg_id=message.from_user.id)),
        )
        identifier = ("@" + client.tg_username) if client.tg_username else ("#" + str(client.tg_id))
        provider_start = start.astimezone(tz=provider.user.tz)
        provider_notification = [
            _("You have a new reservation:\n"),
            state_data["service_name"],
            client.full_name + ", " + identifier,
            _(WDS[date.weekday()])
            + ", "
            + provider_start.strftime(DATE_FORMAT)
            + ", "
            + provider_start.strftime(TIME_FORMAT),
        ]
        provider_chat = await bot.get_chat(provider_id)
        await bot.send_message(chat_id=provider_chat.id, text="\n".join(provider_notification))
        return

    else:
        service_name = message.text.split(", ")[0]
        offset = 0 if datetime.datetime.now(tz=provider.user.tz).time() < provider.end else 1
        await state.update_data(service_name=service_name, offset=offset)

    state_data = await state.get_data()
    provider_tg_id = state_data["provider_id"]
    service_data = await get_service_data(service_name, int(provider_tg_id))

    if not service_data:
        await state.clear()
        await message.answer(_("You've clearly entered something wrong. Please, try again."))
        return

    client_tg_id = message.from_user.id
    day, available_slots, is_day_off, is_vacation = await get_available_hours(
        current_user_tg_id=client_tg_id,
        provider_tg_id=provider_tg_id,
        client_tg_id=client_tg_id,
        service_name=service_name,
        offset=offset,
    )
    date = WEEKDAYS[int(day.weekday())] + ", " + day.strftime(_(DATE_FORMAT))
    markup = ReplyKeyboardMarkup(keyboard=[[]], resize_keyboard=True, one_time_keyboard=True)

    if offset:
        row = [_("Previous day"), _("Today"), _("Next day")]

    else:
        row = [_("Next day")]

    markup.keyboard.append(row)
    time_buttons = []

    for time in available_slots:
        time_string = time.strftime("%H:%M")
        button = KeyboardButton(text=time_string)
        time_buttons.append(button)
    time_button_rows = [list(row) for row in itertools.batched(time_buttons, 3)]

    for row in time_button_rows:
        markup.keyboard.append(row)

    markup.keyboard.append([_("Cancel booking")])
    await state.update_data(date=day)
    await message.answer(
        (_("Please, select the desirable date and time of the reservation.") + "\n" + date),
        reply_markup=markup,
    )
