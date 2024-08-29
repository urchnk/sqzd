from decimal import Decimal

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardMarkup

from apps.services.models import Service
from bot import _
from djmoney.money import Money
from moneyed.l10n import format_money
from tgbot.filters.provider import IsProviderFilter
from tgbot.keyboards.default import get_provider_services_menu
from utils.bot.to_async import add_service, check_service_exists, get_provider_currency, get_user

service_create_router = Router()


class NewServiceStatesGroup(StatesGroup):
    set_name = State()
    set_duration = State()
    set_price = State()


@service_create_router.message(F.text == _("Add service"), IsProviderFilter())
async def create_service(message: Message, state: FSMContext):
    markup = ReplyKeyboardMarkup(keyboard=[[]], resize_keyboard=True)
    markup.keyboard.append([_("Cancel")])
    await state.set_state(NewServiceStatesGroup.set_name)
    await message.answer(_("Please, enter the name of the service:"), reply_markup=markup)


@service_create_router.message(NewServiceStatesGroup.set_name, IsProviderFilter())
async def set_name(message: Message, state: FSMContext):
    markup = ReplyKeyboardMarkup(keyboard=[[]], resize_keyboard=True)
    markup.keyboard.append([_("Cancel")])
    if message.text == _("Cancel"):
        await message.answer(_("Main menu:"), reply_markup=(await get_provider_services_menu()))
        return
    if await check_service_exists(message.text, message.from_user.id):
        await message.answer(
            _("You already have a service this name. Please, choose another."),
            reply_markup=markup,
        )
    else:
        await state.update_data(name=message.text)
        await state.set_state(NewServiceStatesGroup.set_duration)
        await message.answer(
            _("Please, enter the standard duration of this service in minutes:"),
            reply_markup=markup,
        )


@service_create_router.message(NewServiceStatesGroup.set_duration, IsProviderFilter())
async def set_duration(message: Message, state: FSMContext):
    markup = ReplyKeyboardMarkup(keyboard=[[]], resize_keyboard=True)
    markup.keyboard.append([_("Cancel")])
    await state.update_data(duration=message.text)
    await state.set_state(NewServiceStatesGroup.set_price)
    await message.answer(_("Please, enter the price of this service:"), reply_markup=markup)


@service_create_router.message(NewServiceStatesGroup.set_price, IsProviderFilter())
async def finish_adding_service(message: Message, state: FSMContext):
    await state.update_data(price=Money(message.text, currency=await get_provider_currency(message.from_user.id)))
    service_data = await state.get_data()
    name = service_data["name"]
    duration = int(service_data["duration"])
    price = service_data["price"]
    service: Service = await add_service(name=name, duration=duration, price=price, tg_id=message.from_user.id)
    await state.clear()
    await message.answer(
        f"{service.name}\n" + f"{service.duration} " + _("minutes\n") + f"{service.price}",
        reply_markup=get_provider_services_menu(),
    )
