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
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

import environ
from aiohttp import web
from dotenv import load_dotenv
from tgbot.middlewares.debug import AllowedUsersMiddleware

load_dotenv()
env = environ.Env()

logger = logging.getLogger(__name__)

_ = gettext

# Bot token can be obtained via https://t.me/BotFather
TOKEN = env.str("BOT_TOKEN")
ADMINS = env.list("ADMINS")

DEBUG = env.bool("DEBUG")

if not DEBUG:
    HEROKU_APP_NAME = env.str("HEROKU_APP_NAME")
    # Base URL for webhook will be used to generate webhook URL for Telegram,
    # in this example it is used public address with TLS support
    BASE_WEBHOOK_URL = f"https://{HEROKU_APP_NAME}.herokuapp.com"

# Webserver settings
# bind localhost only to prevent any external access
WEB_SERVER_HOST = "0.0.0.0"
# Port for incoming request from reverse proxy. Should be any available port
WEB_SERVER_PORT = env.int("PORT")

# Path to webhook route, on which Telegram will send requests
WEBHOOK_PATH = "/webhook"
# Secret key to validate requests from Telegram (optional)
WEBHOOK_SECRET = env.str("WEBHOOK_SECRET")


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


async def on_startup(bot: Bot) -> None:
    # In case when you have a self-signed SSL certificate, you need to send the certificate
    # itself to Telegram servers for validation purposes
    # (see https://core.telegram.org/bots/self-signed)
    # But if you have a valid SSL certificate, you SHOULD NOT send it to Telegram servers.
    await bot.set_webhook(
        f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}",
        secret_token=WEBHOOK_SECRET,
    )


async def on_shutdown(bot: Bot):
    logging.info("Shutting down...")
    await bot.delete_webhook()
    logging.info("Bye!")


def main_webhook():
    setup_django()

    logging.basicConfig(
        level=logging.INFO,
        format="%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s",
    )
    logger.info("Starting bot")

    include_all_routers(dp)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    app = web.Application()

    # Create an instance of request handler,
    # aiogram has few implementations for different cases of usage
    # In this example we use SimpleRequestHandler which is designed to handle simple cases
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=WEBHOOK_SECRET,
    )
    # Register webhook handler on application
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)

    # Mount dispatcher startup and shutdown hooks to aiohttp application
    setup_application(app, dp, bot=bot)

    # And finally start webserver
    web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)


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
        main_webhook()
    except (KeyboardInterrupt, SystemExit):
        logger.error("Bot stopped!")
