from datetime import time, timedelta

from aiogram import types
from aiogram.types import KeyboardButton

import moneyed
from bot import _
from utils.bot.consts import TIME_INPUT_FORMAT
from utils.bot.to_async import get_provider_clients, get_provider_data, get_provider_services, is_provider


def yes_no():
    return types.ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=_("Yes")), KeyboardButton(text=_("No"))]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def get_provider_main_menu():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=_("Reservations")),
                KeyboardButton(text=_("Services menu")),
            ],
            [
                KeyboardButton(text=_("Breaks & days off")),
                KeyboardButton(text=_("Clients")),
            ],
            [KeyboardButton(text=_("Provider settings"))],
            [KeyboardButton(text=_("My client menu"))],
        ],
        resize_keyboard=True,
    )


def get_provider_settings_menu():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=_("Get my deep link")),
                # KeyboardButton(text=_("Services menu")),
            ],
            # [
            #     KeyboardButton(text=_("Breaks & days off")),
            #     KeyboardButton(text=_("Clients")),
            # ],
            [KeyboardButton(text=_("Back to main menu"))],
        ],
        resize_keyboard=True,
    )


async def get_client_main_menu(tg_id):
    markup = types.ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=_("Upcoming reservations")),
                KeyboardButton(text=_("Past reservations")),
            ]
        ],
        resize_keyboard=True,
    )
    if await is_provider(tg_id):
        markup.keyboard.append([KeyboardButton(text=_("My provider menu"))])

    return markup


async def get_main_menu(tg_id: int):
    if await is_provider(tg_id):
        return get_provider_main_menu()
    else:
        return await get_client_main_menu(tg_id)


def get_provider_services_menu():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=_("Add service")),
                KeyboardButton(text=_("Remove service")),
            ],
            [KeyboardButton(text=_("Back to main menu"))],
        ],
        resize_keyboard=True,
    )


async def get_provider_clients_keyboard(tg_id: int, offset: int = 0):
    markup = types.ReplyKeyboardMarkup(keyboard=[[]], resize_keyboard=True)
    all_clients = [client for client in (await get_provider_clients(tg_id))]

    if all_clients:
        clients = all_clients[offset : (offset + 10)]

        if offset:
            markup.keyboard.append([KeyboardButton(text=_("Previous 10"))])

        for client in clients:
            if client.phone:
                identifier = client.phone
            elif client.tg_username:
                identifier = f"@{client.tg_username}"
            else:
                identifier = f"#{client.tg_id}"

            markup.keyboard.append([KeyboardButton(text=f"{client.full_name}, {identifier}")])

        if all_clients[-1] != clients[-1]:
            markup.keyboard.append([KeyboardButton(text=_("Next 10"))])

    markup.keyboard.append([KeyboardButton(text=_("Back to main menu"))])
    return markup


async def get_provider_services_keyboard(tg_id: int):
    markup = types.ReplyKeyboardMarkup(keyboard=[[]], resize_keyboard=True)
    services = await get_provider_services(tg_id)
    if services:
        for service in services:
            markup.keyboard.append([service.name])
    markup.keyboard.append([KeyboardButton(text=_("Back to main menu"))])
    return markup


def get_provider_breaks_days_off_menu():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=_("Recurring schedule settings")),
            ],
            [
                KeyboardButton(text=_("Breaks")),
                KeyboardButton(text=_("Days off")),
            ],
            [KeyboardButton(text=_("Back to main menu"))],
        ],
        resize_keyboard=True,
    )


def get_provider_recurring_schedule_menu():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=_("Edit lunch time")),
                KeyboardButton(text=_("Edit days off")),
            ],
            [KeyboardButton(text=_("Back to breaks & days off"))],
        ],
        resize_keyboard=True,
    )


async def get_lunch_start_keyboard():
    provider = await get_provider_data()
    span_length = (provider["start"] - provider["end"]) / 15
    slots: list[time] = [provider["start"]]

    for i in range(1, span_length):
        slots.append(provider["start"] + timedelta(minutes=(provider["slot"] * i)))

    cursor = 0
    buttons = []
    row = []

    for slot in slots:
        row.append(KeyboardButton(text=slot.strftime(TIME_INPUT_FORMAT)))
        cursor += 1
        if cursor == 5:
            buttons.append(row)
            cursor = 0

    return types.ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def get_provider_breaks_menu():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=_("Set a break")),
                KeyboardButton(text=_("Cancel a break")),
            ],
            [KeyboardButton(text=_("Back to breaks & days off"))],
        ],
        resize_keyboard=True,
    )


def get_duration_choices_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="15"),
                KeyboardButton(text="30"),
                KeyboardButton(text="45"),
            ],
            [
                KeyboardButton(text="60"),
                KeyboardButton(text="90"),
                KeyboardButton(text="120"),
            ],
        ],
        resize_keyboard=True,
    )


def get_currencies_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=_("Ukrainian Hryvnia") + ", UAH"),
                KeyboardButton(text=_("Euro") + ", EUR"),
            ],
            [
                KeyboardButton(text=_("Polish Zloty") + ", PLN"),
                KeyboardButton(text=_("Czech Koruna") + ", CZK"),
            ],
            [
                KeyboardButton(text=_("US Dollar") + ", USD"),
                KeyboardButton(text=_("Canadian dollar") + ", CAD"),
            ],
            [
                KeyboardButton(text=_("British Pound") + ", GBP"),
                KeyboardButton(text=_("Swedish Krona") + ", SEK"),
            ],
            [
                KeyboardButton(text=_("Norwegian Krone'") + ", NOK"),
                KeyboardButton(text=_("Danish Krone") + ", DKK"),
            ],
            [
                KeyboardButton(text=_("Romanian Leu") + ", RON"),
                KeyboardButton(text=_("Moldovan Leu") + ", MDL"),
            ],
        ],
        resize_keyboard=True,
    )
