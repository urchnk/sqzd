from datetime import time, timedelta

from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot import _
from utils.bot.consts import TIME_INPUT_FORMAT
from utils.bot.to_async import get_provider_clients, get_provider_data, get_provider_services, is_provider


def yes_no():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(
        text=_("Yes"),
        callback_data="yes",
    )
    keyboard.button(
        text=_("No"),
        callback_data="no",
    )
    keyboard.adjust(2)
    return keyboard.as_markup()


def cancel():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(
        text=_("Cancel"),
        callback_data="main_menu",
    )
    keyboard.button(
        text=_("No"),
        callback_data="no",
    )
    keyboard.adjust(2)
    return keyboard.as_markup()


def get_provider_main_menu():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(
        text=_("Reservations"),
        callback_data="reservations",
    )
    keyboard.button(
        text=_("Services menu"),
        callback_data="services_menu",
    )
    keyboard.button(
        text=_("Breaks & days off"),
        callback_data="breaks_and_days_off",
    )
    keyboard.button(
        text=_("Clients"),
        callback_data="clients",
    )
    keyboard.button(
        text=_("Provider settings"),
        callback_data="provider_settings",
    )
    keyboard.button(
        text=_("My client menu"),
        callback_data="client_menu",
    )
    keyboard.adjust(2)
    return keyboard.as_markup()


def get_provider_settings_menu():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(
        text=_("Get my deep link"),
        callback_data="my_deep_link",
    )
    keyboard.button(
        text=_("Back to main menu"),
        callback_data="main_menu",
    )
    keyboard.adjust(2)
    return keyboard.as_markup()


async def get_client_main_menu(tg_id):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(
        text=_("Upcoming reservations"),
        callback_data="upcoming_reservations",
    )
    keyboard.button(
        text=_("Past reservations"),
        callback_data="past_reservations",
    )

    if await is_provider(tg_id):
        keyboard.button(
            text=_("My provider menu"),
            callback_data="provider_menu",
        )
    keyboard.adjust(2)
    return keyboard.as_markup()


async def get_provider_clients_keyboard(tg_id: int, offset: int = 0):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(
        text=_("Get my deep link"),
        callback_data="my_deep_link",
    )
    all_clients = [client for client in (await get_provider_clients(tg_id))]

    if all_clients:
        clients = all_clients[offset : (offset + 10)]

        if offset:
            keyboard.button(
                text=_("Previous 10"),
                callback_data="previous_10",
            )

        if all_clients[-1] != clients[-1]:
            keyboard.button(
                text=_("Next 10"),
                callback_data="next_10",
            )

        for client in clients:
            if client.phone:
                identifier = client.phone
            elif client.tg_username:
                identifier = f"@{client.tg_username}"
            else:
                identifier = f"#{client.tg_id}"

            keyboard.button(
                text=f"{client.full_name}",
                callback_data=str(identifier),
            )

    keyboard.button(
        text=_("Back to main menu"),
        callback_data="main_menu",
    )

    keyboard.adjust(2)
    return keyboard.as_markup()


class ServiceCallback(CallbackData, prefix="service"):
    _id: int
    name: str


async def get_provider_services_keyboard(tg_id: int):
    keyboard = InlineKeyboardBuilder()
    services = await get_provider_services(tg_id)

    if services:
        for service in services:
            keyboard.button(
                text=(service.name + ", " + str(service.price.amount) + " " + str(service.price.currency)),
                callback_data=ServiceCallback(_id=service.id),
            )

    keyboard.button(
        text=_("Back to main menu"),
        callback_data="main_menu",
    )
    keyboard.adjust(2)
    return keyboard.as_markup()


def get_provider_breaks_days_off_menu():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(
        text=_("Edit lunch time"),
        callback_data="edit_lunch_time",
    )
    keyboard.button(
        text=_("Edit weekly days off"),
        callback_data="edit_weekly_days_off",
    )
    keyboard.button(
        text=_("Breaks"),
        callback_data="breaks_settings",
    )
    keyboard.button(
        text=_("Days off"),
        callback_data="days_off__settings",
    )
    keyboard.button(
        text=_("Back to main menu"),
        callback_data="main_menu",
    )
    keyboard.adjust(2)
    return keyboard.as_markup()


class SlotCallback(CallbackData, prefix="slot"):
    start: time


async def get_lunch_start_keyboard():
    provider = await get_provider_data()
    span_length = (provider["start"] - provider["end"]) / provider["slot"]
    slots: list[time] = [provider["start"]]

    for i in range(1, span_length):
        slots.append(provider["start"] + timedelta(minutes=(provider["slot"] * i)))

    keyboard = InlineKeyboardBuilder()

    for slot in slots:
        keyboard.button(
            text=slot.strftime(TIME_INPUT_FORMAT),
            callback_data=SlotCallback(start=slot),
        )

    keyboard.adjust(4)
    return keyboard.as_markup()


def get_provider_breaks_menu():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(
        text=_("Set a break"),
        callback_data="set_a_break",
    )
    keyboard.button(
        text=_("Cancel a break"),
        callback_data="cancel_a_break",
    )
    keyboard.button(
        text=_("Back to main menu"),
        callback_data="main_menu",
    )
    keyboard.adjust(2)
    return keyboard.as_markup()


def get_duration_choices_keyboard():
    keyboard = InlineKeyboardBuilder()
    for duration in [15, 30, 45, 60, 90, 120]:
        keyboard.button(
            text=str(duration),
            callback_data="duration",
        )
    keyboard.adjust(3)
    return keyboard.as_markup()


class CurrencyCallback(CallbackData, prefix="currency"):
    code: str


def get_currencies_keyboard():
    keyboard = InlineKeyboardBuilder()
    currencies = [
        {"name": _("Ukrainian Hryvnia"), "code": "UAH"},
        {"name": _("Euro"), "code": "EUR"},
        {"name": _("Polish Zloty"), "code": "PLN"},
        {"name": _("Czech Koruna"), "code": "CZK"},
        {"name": _("US Dollar"), "code": "USD"},
        {"name": _("Canadian dollar"), "code": "CAD"},
        {"name": _("British Pound"), "code": "GBP"},
        {"name": _("Swedish Krona"), "code": "SEK"},
        {"name": _("Norwegian Krone'"), "code": "NOK"},
        {"name": _("Danish Krone"), "code": "DKK"},
        {"name": _("Romanian Leu"), "code": "RON"},
        {"name": _("Moldovan Leu"), "code": "MDL"},
    ]
    for currency in currencies:
        keyboard.button(
            text=currency["name"],
            callback_data=CurrencyCallback(code=currency["code"]),
        )
    return keyboard.as_markup()
