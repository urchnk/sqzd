#!/usr/bin/env python
import asyncio
import logging
import os

from django.conf import settings
from django.utils.translation import gettext

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

import environ
from dotenv import load_dotenv
from tgbot.middlewares.debug import AllowedUsersMiddleware

load_dotenv()
env = environ.Env()

logger = logging.getLogger(__name__)

_ = gettext

# Bot token can be obtained via https://t.me/BotFather
TOKEN = env.str("BOT_TOKEN")
ADMINS = env.list("ADMINS")


def setup_django():
    import django

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    os.environ.update({"DJANGO_ALLOW_ASYNC_UNSAFE": "true"})

    django.setup()


storage = MemoryStorage()
bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher(storage=storage)

if settings.DEBUG:
    allowed_users = settings.ALLOWED_TG_USERS
    dp.message.middleware(AllowedUsersMiddleware(allowed_users))


def include_all_routers(_dp: Dispatcher):
    from tgbot.handlers.admin import admin_router
    from tgbot.handlers.clients_list import clients_list_router
    from tgbot.handlers.help import help_router
    from tgbot.handlers.menu import menu_router
    from tgbot.handlers.provider_breaks import provider_breaks_router
    from tgbot.handlers.provider_create import provider_create_router
    from tgbot.handlers.provider_schedule import provider_schedule_router
    from tgbot.handlers.provider_settings import provider_settings_router
    from tgbot.handlers.reservation_create import reservation_create_router
    from tgbot.handlers.service_create import service_create_router
    from tgbot.handlers.service_remove import service_remove_router
    from tgbot.handlers.services_menu import services_menu_router
    from tgbot.handlers.start import start_router

    _dp.include_routers(
        # admin_router,
        clients_list_router,
        help_router,
        menu_router,
        provider_breaks_router,
        provider_create_router,
        provider_schedule_router,
        reservation_create_router,
        service_create_router,
        service_remove_router,
        services_menu_router,
        start_router,
        provider_settings_router,
    )


async def main():
    setup_django()

    logging.basicConfig(
        level=logging.INFO,
        format="%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s",
    )
    logger.info("Starting bot")

    include_all_routers(dp)

    try:
        await dp.start_polling(bot)
    finally:
        await dp.storage.close()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.error("Bot stopped!")
