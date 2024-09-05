import datetime
import itertools

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup

from bot import _
from tgbot.filters.provider import IsProviderFilter
from tgbot.keyboards.default import (
    get_provider_clients_keyboard,
    get_provider_main_menu,
    get_provider_services_keyboard,
)
from utils.bot.consts import DATE_FORMAT, TIME_FORMAT, WDS, WEEKDAYS
from utils.bot.services import get_provider_events_as_message
from utils.bot.to_async import (
    create_user,
    get_available_hours,
    get_or_create_user,
    get_provider,
    get_service_data,
    get_user,
    set_reservation,
)
from utils.misc.validation import is_phone_number

provider_schedule_router = Router()


class ProviderReservationsStatesGroup(StatesGroup):
    list_reservations = State()
    new_reservation = State()
    choose_client = State()
    set_name = State()
    set_phone = State()
    choose_service = State()
    choose_datetime = State()


@provider_schedule_router.message(
    F.text.in_([_("Reservations"), _("See schedule")]),
    IsProviderFilter(),
)
async def provider_list_reservations(message: Message, state: FSMContext):
    await state.set_state(ProviderReservationsStatesGroup.list_reservations)
    provider = await get_provider(tg_id=message.from_user.id)
    offset = 0 if datetime.datetime.now(tz=provider.user.tz).time() < provider.end else 1
    await state.update_data(offset=offset)

    events_as_message = await get_provider_events_as_message(message.from_user.id, offset=0)
    markup = ReplyKeyboardMarkup(keyboard=[[]], resize_keyboard=True, one_time_keyboard=True)
    markup.keyboard.append([_("Previous day"), _("Next day")])
    markup.keyboard.append([_("New reservation")])
    markup.keyboard.append([_("Back to provider menu")])
    await message.answer(events_as_message, reply_markup=markup)


@provider_schedule_router.message(
    F.text == _("New reservation"),
    IsProviderFilter(),
)
async def provider_new_reservation(message: Message, state: FSMContext):
    markup = ReplyKeyboardMarkup(keyboard=[[]], resize_keyboard=True, one_time_keyboard=True)
    markup.keyboard.append([KeyboardButton(text=_("Choose client"))])
    markup.keyboard.append([KeyboardButton(text=_("New client"))])
    markup.keyboard.append([KeyboardButton(text=_("Back to provider menu"))])
    await state.set_state(ProviderReservationsStatesGroup.new_reservation)
    await state.update_data(offset=0)
    await message.answer(_("New reservation:"), reply_markup=markup)


@provider_schedule_router.message(
    ProviderReservationsStatesGroup.list_reservations,
    IsProviderFilter(),
)
async def provider_surf_reservations(message: Message, state: FSMContext):
    state_data = await state.get_data()
    offset = state_data["offset"]
    if message.text == _("Previous day"):
        offset = offset - 1
        await state.update_data(offset=offset)
    elif message.text == _("Today"):
        offset = 0
        await state.update_data(offset=offset)
    elif message.text == _("Next day"):
        offset = offset + 1
        await state.update_data(offset=offset)
    elif message.text == _("Back to provider menu"):
        await state.clear()
        await message.answer(_("Main menu:"), reply_markup=get_provider_main_menu())
        return
    else:
        offset = state_data["offset"]
        await state.update_data(offset=offset)
    events_as_message = await get_provider_events_as_message(message.from_user.id, offset=offset)

    markup = ReplyKeyboardMarkup(keyboard=[[]], resize_keyboard=True, one_time_keyboard=True)
    row = [_("Previous day")]
    if offset != 0:
        row.append(_("Today"))
    row.append(_("Next day"))
    markup.keyboard.append(row)
    markup.keyboard.append([_("New reservation")])
    markup.keyboard.append([_("Back to provider menu")])
    await message.answer(
        events_as_message,
        reply_markup=markup,
    )


@provider_schedule_router.message(
    ProviderReservationsStatesGroup.new_reservation,
    IsProviderFilter(),
)
async def provider_new_reservation_choose_client(message: Message, state: FSMContext):
    state_data = await state.get_data()

    if message.text == _("Choose client"):
        offset = 0

    elif message.text == _("Next 10"):
        offset = state_data["offset"] + 10

    elif message.text == _("Previous 10"):
        offset = state_data["offset"] - 10

    elif message.text == _("New client"):
        await state.set_state(ProviderReservationsStatesGroup.set_name)
        markup = ReplyKeyboardMarkup(keyboard=[[]], resize_keyboard=True)
        markup.keyboard.append([KeyboardButton(text=(_("Back to provider menu")))])
        await message.answer(
            _("Please, enter the new client's name (or just share a contact with a phone number):"), reply_markup=markup
        )
        return

    else:
        try:
            identifier = message.text.split(", ")[1]
        except AttributeError:
            await message.answer(_("You've entered something wrong. Please, try again."))
            return
        phone = username = tg_id = ""
        if identifier[0] == "@":
            username = identifier.lstrip("@")
        elif identifier[0] == "+":
            phone = identifier
        elif identifier[0] == "#":
            tg_id = int(identifier.lstrip("#"))
        else:
            return await message.answer(_("You've entered something wrong. Please, try again."))

        if user := await get_user(tg_id=tg_id, username=username, phone=phone):
            await state.update_data(username=user.username, client_id=user.id, client_tg_id=user.tg_id, phone=phone)
            markup = await get_provider_services_keyboard(message.from_user.id)
            if len(markup.keyboard) > 1:
                await state.set_state(ProviderReservationsStatesGroup.choose_service)
                await message.answer(_("Please, choose a service:"), reply_markup=markup)
                return
            else:
                return await message.answer(
                    _("You have no services listed at the moment."),
                    reply_markup=markup,
                )
        else:
            return await message.answer(_("You've entered something wrong. Please, try again."))

    await state.update_data(offset=offset)
    markup = await get_provider_clients_keyboard(message.from_user.id, offset=offset)
    await message.answer(_("Please, choose a client:"), reply_markup=markup)


@provider_schedule_router.message(
    ProviderReservationsStatesGroup.set_name,
    IsProviderFilter(),
)
async def provider_new_reservation_new_client_name_or_contact(message: Message, state: FSMContext):
    if message.contact:
        await state.update_data(
            from_contact={
                "first_name": message.contact.first_name,
                "last_name": message.contact.last_name,
                "phone_number": message.contact.phone_number,
                "client_tg_id": message.contact.user_id,
            }
        )
        await state.set_state(ProviderReservationsStatesGroup.choose_service)
        await message.answer(
            _("Client:\n")
            + f"{message.contact.first_name} {message.contact.last_name}\n"
            + f"{message.contact.phone_number}\n",
            reply_markup=(await get_provider_services_keyboard(message.from_user.id)),
        )

    else:
        name = message.text.split(" ")
        if len(name) > 1:
            await state.update_data(first_name=" ".join(name[:-1]))
            await state.update_data(last_name=name[-1])
        else:
            await state.update_data(first_name=message.text)
        await state.set_state(ProviderReservationsStatesGroup.set_phone)
        markup = ReplyKeyboardMarkup(keyboard=[[]], resize_keyboard=True)
        markup.keyboard.append([KeyboardButton(text=(_("Back to provider menu")))])
        await message.answer(
            _("Please, enter the new client's phone number:"),
            reply_markup=markup,
        )


@provider_schedule_router.message(
    ProviderReservationsStatesGroup.set_phone,
    IsProviderFilter(),
)
async def provider_new_reservation_new_client_finish(message: Message, state: FSMContext):
    state_data = await state.get_data()
    phone = message.text

    if not is_phone_number(phone):
        await message.answer(_("You've entered something wrong. Please, try again."))

    user = await create_user(state_data["first_name"], (state_data.get("last_name") or ""), phone)
    await state.update_data(client_id=user.pk, phone=phone)
    await state.set_state(ProviderReservationsStatesGroup.choose_service)
    markup = await get_provider_services_keyboard(message.from_user.id)
    await message.answer(_("Please, choose a service"), reply_markup=markup)


@provider_schedule_router.message(
    ProviderReservationsStatesGroup.choose_service,
    IsProviderFilter(),
)
async def provider_new_reservation_choose_datetime(message: Message, state: FSMContext):
    state_data = await state.get_data()
    provider_id = message.from_user.id
    provider = await get_provider(provider_id)
    today_offset = 0 if datetime.datetime.now(tz=provider.user.tz).time() < provider.end else 1
    if message.text == _("Next day"):
        service_name = state_data["service_name"]
        offset = state_data["offset"] + 1
        await state.update_data(offset=offset)
    elif message.text == _("Previous day"):
        service_name = state_data["service_name"]
        offset = state_data["offset"] - 1
        await state.update_data(offset=offset)
    elif message.text == _("Today"):
        service_name = state_data["service_name"]
        await state.update_data(offset=today_offset)
    elif message.text == _("Cancel"):
        await state.clear()
        await message.answer(
            _("You've canceled the reservation setting."),
            reply_markup=get_provider_main_menu(),
        )
        return
    elif len(message.text) == 5 and (":" in message.text):
        state_data = await state.get_data()
        if contact := state_data.get("from_contact"):
            client = await get_or_create_user(
                tg_id=contact["client_tg_id"],
                first_name=contact["first_name"],
                last_name=contact["last_name"],
                phone=contact["phone_number"],
                provider_created=True,
            )
        else:
            client = await get_or_create_user(
                first_name=state_data.get("first_name"),
                last_name=state_data.get("last_name"),
                phone=state_data.get("phone"),
                provider_created=True,
                tz=provider.user.tz,
            )
        await state.update_data(client_id=client.pk)
        await state.update_data(client_tg_id=client.tg_id)
        service_data = await get_service_data(state_data["service_name"], provider_id)
        hour = int(message.text.split(":")[0])
        minute = int(message.text.split(":")[1])
        date: datetime.date = state_data["date"]
        tz = provider.user.tz
        start = datetime.datetime.combine(date, datetime.time(hour=hour, minute=minute), tzinfo=tz)
        await set_reservation(
            client=client,
            provider=provider,
            service_id=service_data["id"],
            start=start,
        )
        await state.clear()
        await message.answer(
            (
                _("You have set the following reservation:\n")
                + _("Service: {service}\n").format(service=state_data["service_name"])
                + _("Client: {name} {username}\n").format(
                    name=client.full_name, username=((", @" + client.tg_username) if client.tg_username else "")
                )
                + (client.phone + "\n")
                if client.phone
                else (
                    "" + ("@" + client.tg_username)
                    if client.tg_username
                    else ""
                    + _(WDS[date.weekday()])
                    + ", "
                    + start.strftime(DATE_FORMAT)
                    + ", "
                    + start.strftime(TIME_FORMAT)
                )
            ),
            reply_markup=get_provider_main_menu(),
        )
        return
    else:
        service_name = message.text.split(", ")[0]
        offset = 0
        await state.update_data(service_name=service_name, offset=today_offset)
    state_data = await state.get_data()
    provider_tg_id = message.from_user.id
    service_data = await get_service_data(service_name, int(provider_tg_id))
    if not service_data:
        await state.clear()
        await message.answer(_("You've clearly entered something wrong. Please, try again."))
        return

    day, available_slots, is_day_off, is_vacation = await get_available_hours(
        current_user_tg_id=provider_tg_id,
        provider_tg_id=provider_tg_id,
        service_name=service_name,
        offset=state_data["offset"],
    )
    date = WEEKDAYS[int(day.weekday())] + ", " + day.strftime(DATE_FORMAT)
    markup = ReplyKeyboardMarkup(keyboard=[[]], resize_keyboard=True, one_time_keyboard=True)
    nav = [KeyboardButton(text=(_("Previous day")))]
    if offset:
        nav.append(KeyboardButton(text=(_("Today"))))
    nav.append(KeyboardButton(text=(_("Next day"))))
    markup.keyboard.append(nav)
    if is_day_off:
        text = _("You have a day-off.")
    elif is_vacation:
        text = _("You have a vacation.")
    else:
        time_buttons = []
        for time in available_slots:
            time_string = time.strftime("%H:%M")
            button = KeyboardButton(text=time_string)
            time_buttons.append(button)
        time_button_rows = [list(row) for row in itertools.batched(time_buttons, 3)]
        for row in time_button_rows:
            markup.keyboard.append(row)
        text = _("Please, select the desirable date and time of the reservation.") + "\n" + date
    markup.keyboard.append([KeyboardButton(text=(_("Cancel")))])
    await state.update_data(date=day)
    await message.answer(text, reply_markup=markup)
