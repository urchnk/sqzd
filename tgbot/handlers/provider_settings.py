from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup
from aiogram.utils.deep_linking import create_start_link, encode_payload

from bot import _, bot
from tgbot.filters.provider import IsProviderFilter
from tgbot.keyboards.default import get_provider_settings_menu

provider_settings_router = Router(name="menu")


@provider_settings_router.message(
    F.text.in_(
        {
            _("Provider settings"),
            _("Back to provider settings"),
        }
    ),
    IsProviderFilter(),
)
async def provider_settings(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("⚙️ " + _("Provider settings:"), reply_markup=get_provider_settings_menu())


@provider_settings_router.message(
    F.text == _("Get my deep link"),
    IsProviderFilter(),
)
async def my_deep_link(message: Message, state: FSMContext):
    deep_link = await create_start_link(payload=encode_payload(str(message.from_user.id)), bot=bot)
    markup = ReplyKeyboardMarkup(keyboard=[[]], resize_keyboard=True)
    markup.keyboard.append([KeyboardButton(text=_("Back to provider settings"))])
    await message.answer("Your deep link:\n" + deep_link, reply_markup=get_provider_settings_menu())
