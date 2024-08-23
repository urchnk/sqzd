from aiogram.types import BotCommand


async def set_default_commands():
    from bot import _, bot

    await bot.set_my_commands(
        [
            BotCommand(command="start", description=_("Start bot")),
            BotCommand(command="register_provider", description=_("Become a provider")),
            BotCommand(command="help", description=_("Get help")),
        ]
    )
