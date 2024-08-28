from datetime import datetime

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
from utils.bot.consts import DATE_FORMAT, TIME_FORMAT, WEEKDAYS
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
    await state.update_data(offset=0)

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
        phone = username = ""
        if identifier[0] == "@":
            username = identifier.lstrip("@")
        elif identifier[0] == "+":
            phone = identifier
        else:
            return await message.answer(_("You've entered something wrong. Please, try again."))

        if user := await get_user(username=username, phone=phone):
            await state.update_data(username=user.username, client_id=user.id)
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
        return

    name = message.text.split(" ")
    if len(name) > 1:
        await state.update_data(first_name=" ".join(name[:-1]))
        await state.update_data(last_name=name[-1])
    else:
        await state.update_data(first_name=message.text)
    await state.set_state(ProviderReservationsStatesGroup.set_phone)
    markup = ReplyKeyboardMarkup(keyboard=[[]], resize_keyboard=True)
    markup.keyboard.append([KeyboardButton(text=(_("Leave it empty")))])
    markup.keyboard.append([KeyboardButton(text=(_("Back to provider menu")))])
    await message.answer(
        _("Please, enter the new client's phone number (or leave it empty):"),
        reply_markup=markup,
    )


@provider_schedule_router.message(
    ProviderReservationsStatesGroup.set_phone,
    IsProviderFilter(),
)
async def provider_new_reservation_new_client_finish(message: Message, state: FSMContext):
    state_data = await state.get_data()
    if message.text == _("Leave it empty"):
        phone = ""
    else:
        phone = message.text
    user = await create_user(state_data["first_name"], (state_data.get("last_name") or ""), phone)
    await state.update_data(client_id=user.id)
    await state.set_state(ProviderReservationsStatesGroup.choose_service)
    markup = await get_provider_services_keyboard(message.from_user.id)
    await message.answer(_("Please, choose a service"), reply_markup=markup)


@provider_schedule_router.message(
    ProviderReservationsStatesGroup.choose_service,
    IsProviderFilter(),
)
async def provider_new_reservation_choose_datetime(message: Message, state: FSMContext):
    state_data = await state.get_data()
    if message.text == _("Next day"):
        service_name = state_data["service_name"]
        offset = state_data["offset"] + 1
        await state.update_data(offset=offset)
    elif message.text == _("Previous day"):
        service_name = state_data["service_name"]
        offset = state_data["offset"] - 1
        await state.update_data(offset=offset)
    elif message.text == _("Cancel"):
        await state.clear()
        await message.answer(
            _("You've canceled the reservation setting."),
            reply_markup=get_provider_main_menu(),
        )
        return
    elif message.text.split(",")[0] in WEEKDAYS.values():
        state_data = await state.get_data()
        provider_id = message.from_user.id
        provider = await get_provider(message.from_user.id)
        client = await get_user(user_id=state_data.get("client_id"))
        await state.update_data(client_id=client.id)
        service_data = await get_service_data(state_data["service_name"], provider_id)
        weekday, strdate, strtime = message.text.split(", ")
        start_unaware = datetime.strptime((strdate + strtime), DATE_FORMAT + TIME_FORMAT)
        tz = provider.uzer.tz
        start = start_unaware.replace(tzinfo=tz)
        await set_reservation(
            client=client,
            provider=provider,
            service_id=service_data["id"],
            start=start,
        )
        await state.clear()
        await message.answer(
            _("You have set the following reservation:\n")
            + _("Service: {service}\n").format(service=state_data["service_name"])
            + _("Client: {name} {username}\n").format(
                name=client.full_name, username=((", @" + client.tg_username) if client.tg_username else "")
            )
            + _("Date and time: {weekday}, {strdate}, {strtime}").format(
                weekday=weekday, strdate=strdate, strtime=strtime
            ),
            reply_markup=get_provider_main_menu(),
        )
        return
    else:
        service_name = message.text
        offset = 0
        await state.update_data(service_name=service_name, offset=offset)
    state_data = await state.get_data()
    provider_id = message.from_user.id
    service_data = await get_service_data(service_name, int(provider_id))
    if not service_data:
        await state.clear()
        await message.answer(_("You've clearly entered something wrong. Please, try again."))
        return
    if contact := state_data.get("from_contact"):
        client = await get_or_create_user(
            tg_id=contact["client_tg_id"],
            first_name=contact["first_name"],
            last_name=contact["last_name"],
            phone=contact["phone_number"],
        )
        client_id = client.id
        await state.update_data(client_id=client.id)
    else:
        client_id = state_data.get("client_id")
    client_tg_id = state_data.get("client_tg_id")
    day, available_slots, is_day_off, is_vacation = await get_available_hours(
        tg_id=provider_id, client_id=client_id, client_tg_id=client_tg_id, service_name=service_name, offset=offset
    )
    date = WEEKDAYS[int(day.weekday())] + ", " + day.strftime(DATE_FORMAT)
    markup = ReplyKeyboardMarkup(keyboard=[[]], resize_keyboard=True, one_time_keyboard=True)
    for time in available_slots:
        time_string = time.strftime(TIME_FORMAT)
        button = KeyboardButton(text=f"{date}, {time_string}")
        markup.keyboard.append([button])
    if offset:
        markup.keyboard.append([KeyboardButton(text=(_("Previous day")))])
    markup.keyboard.append([KeyboardButton(text=(_("Next day")))])
    markup.keyboard.append([KeyboardButton(text=(_("Cancel")))])
    await message.answer(
        _("Please, select the desirable date and time of the reservation."),
        reply_markup=markup,
    )
