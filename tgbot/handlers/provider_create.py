from datetime import datetime

from django.conf import settings

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message, ReplyKeyboardMarkup
from aiogram.utils.deep_linking import create_start_link

import moneyed
import requests
from aiogram_i18n.types import KeyboardButton
from bot import IPGEOLOCATION_API_KEY, _
from requests.adapters import HTTPAdapter
from tgbot.keyboards.inline import get_client_main_menu, get_currencies_keyboard, get_provider_main_menu, yes_no
from urllib3 import Retry
from utils.bot.consts import TIME_FORMAT, TIME_INPUT_FORMAT
from utils.bot.to_async import add_provider_to_user, is_provider
from utils.misc.validation import is_phone_number, normalize_email

provider_create_router = Router()


class NewProviderStatesGroup(StatesGroup):
    provider_confirmed = State()
    set_phone_number = State()
    set_email = State()
    set_timezone = State()
    set_currency = State()
    set_start = State()
    set_end = State()


start_options = ["7:00", "8:00", "9:00", "10:00"]
end_options = ["16:00", "17:00", "18:00", "19:00"]


@provider_create_router.message(Command(commands="register_provider"))
async def register_provider(message: Message, state: FSMContext):
    if await is_provider(message.from_user.id):
        await message.answer(
            _("You are already registered as a provider."),
            reply_markup=get_provider_main_menu(),
        )
    else:
        await state.set_state(NewProviderStatesGroup.provider_confirmed)
        await message.answer(_("Do you want to register yourself as a provider?"), reply_markup=yes_no())


@provider_create_router.callback_query(NewProviderStatesGroup.provider_confirmed)
async def register_provider_start(query: CallbackQuery, state: FSMContext):
    await query.answer()
    if query.data == "yes":
        await state.set_state(NewProviderStatesGroup.set_phone_number)
        await query.message.edit_text(
            text=_("Please, enter your phone number:"),
        )
    elif query.data == "no":
        await state.clear()
        await query.message.edit_text(
            text=_("You've canceled the provider registration process."),
            reply_markup=await get_client_main_menu(query.from_user.id),
        )
    else:
        return


@provider_create_router.callback_query(NewProviderStatesGroup.set_phone_number)
async def set_phone_number(message: Message, state: FSMContext):
    if not is_phone_number(message.text):
        await message.answer(_("You've entered something wrong. Please, try again."))
    else:
        await state.update_data(phone=message.text)
        await state.set_state(NewProviderStatesGroup.set_email)
        await message.answer(_("Please, enter your email:"))


@provider_create_router.message(NewProviderStatesGroup.set_email)
async def set_email(message: Message, state: FSMContext):
    email = normalize_email(message.text)
    if not email:
        await message.answer(_("You've entered something wrong. Please, try again."))
    else:

        await state.update_data(email=email)
        markup = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=_("Cancel"))]], resize_keyboard=True, one_time_keyboard=True
        )
        await state.set_state(NewProviderStatesGroup.set_timezone)
        await message.answer(_("Please, share your location, so we can set your timezone."), reply_markup=markup)


@provider_create_router.message(NewProviderStatesGroup.set_timezone)
async def set_timezone(message: Message, state: FSMContext):
    if not message.location:
        await message.answer(_("You've sent something wrong. Please, try again."))
    else:

        latitude = message.location.latitude
        longitude = message.location.longitude
        try:
            session = requests.Session()
            retry = Retry(connect=5, backoff_factor=0.5)
            adapter = HTTPAdapter(max_retries=retry)
            session.mount("https://", adapter)

            result = session.get(
                f"https://api.ipgeolocation.io/timezone?apiKey={IPGEOLOCATION_API_KEY}&lat={latitude}&long={longitude}"
            )
            tz = result.json()["timezone"]

        except requests.exceptions.ConnectionError:
            tz = "Europe/Kyiv"  # TODO: Notify provider about this somehow (or think of something more elegant)

        await state.update_data(tz=tz)
        await state.set_state(NewProviderStatesGroup.set_currency)
        await message.answer(
            _("What currency do you charge clients in?"),
            reply_markup=get_currencies_keyboard(),
        )


@provider_create_router.message(NewProviderStatesGroup.set_currency)
async def set_currency(message: Message, state: FSMContext):
    if (currency := message.text.split(", ")[1]) not in settings.CURRENCIES:
        await message.answer(
            _("You've sent something wrong. Please, try again."), reply_markup=get_currencies_keyboard()
        )
    else:
        await state.update_data(currency=currency)
        markup = ReplyKeyboardMarkup(keyboard=[[]], resize_keyboard=True, one_time_keyboard=True)
        markup.keyboard.append([KeyboardButton(text=button) for button in start_options])
        await state.set_state(NewProviderStatesGroup.set_start)
        await message.answer(_("At what time do you begin your working day?"), reply_markup=markup)


@provider_create_router.message(NewProviderStatesGroup.set_start)
async def set_start(message: Message, state: FSMContext):
    try:
        start = datetime.strptime(message.text, TIME_INPUT_FORMAT).time()
    except ValueError:
        markup = ReplyKeyboardMarkup(keyboard=[[]], resize_keyboard=True, one_time_keyboard=True)
        markup.keyboard.append([KeyboardButton(text=button) for button in start_options])
        return await message.answer(_("You've entered something wrong. Please, try again."), reply_markup=markup)
    await state.update_data(start=start)
    markup = ReplyKeyboardMarkup(keyboard=[[]], resize_keyboard=True, one_time_keyboard=True)
    markup.keyboard.append([KeyboardButton(text=button) for button in end_options])
    await state.set_state(NewProviderStatesGroup.set_end)
    await message.answer(_("At what time do you finish your working day?"), reply_markup=markup)


@provider_create_router.message(NewProviderStatesGroup.set_end)
async def set_end(message: Message, state: FSMContext):
    try:
        end = datetime.strptime(message.text, TIME_INPUT_FORMAT).time()
    except ValueError:
        markup = ReplyKeyboardMarkup(keyboard=[[]], resize_keyboard=True, one_time_keyboard=True)
        markup.keyboard.append([KeyboardButton(text=button) for button in end_options])
        return await message.answer(_("You've entered something wrong. Please, try again."), reply_markup=markup)

    from bot import bot

    provider_info = await state.get_data()
    start = provider_info["start"]
    end = end
    phone = provider_info["phone"]
    email = provider_info["email"]
    tz = provider_info["tz"]
    currency = provider_info["currency"]
    await add_provider_to_user(
        message.from_user.id,
        email=email,
        phone=phone,
        start=start,
        end=end,
        tz=tz,
        currency=currency,
    )
    booking_link = await create_start_link(bot, str(message.from_user.id), encode=True)
    await state.clear()
    start = start.strftime(TIME_FORMAT)
    end = end.strftime(TIME_FORMAT)
    await message.answer(
        _("You have been registered as a provider with the following info:\n\n")
        + _("Phone number: {phone}\n").format(phone=phone)
        + f"Email: {email}\n"
        + _("Time zone: ")
        + tz
        + "\n"
        + _("Currency: ")
        + _(moneyed.get_currency(currency).name)
        + "\n"
        + _("Working day from {start} to {end}\n").format(start=start, end=end)
        + _("Your link for booking: {booking_link}").format(booking_link=booking_link),
        reply_markup=get_provider_main_menu(),
    )
