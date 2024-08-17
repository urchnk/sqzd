from aiogram import types


async def get_locale(tg_id):
    from utils.bot.to_async import get_user

    return (await get_user(tg_id)).locale
