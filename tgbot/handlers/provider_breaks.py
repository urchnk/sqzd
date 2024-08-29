from datetime import date, datetime

from aiogram import F, Router
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup

from apps.scheduler.services import get_provider_week_overview
from bot import _
from tgbot.filters.provider import IsProviderFilter
from tgbot.keyboards.default import (
    get_duration_choices_keyboard,
    get_main_menu,
    get_provider_breaks_days_off_menu,
    get_provider_breaks_menu,
    get_provider_recurring_schedule_menu,
)
from utils.bot.consts import DATE_FORMAT, TIME_FORMAT, TIME_INPUT_FORMAT, WDS, WDS_REV, WEEKDAYS
from utils.bot.services import (
    get_provider_breaks_as_message,
    get_provider_lunch_as_message,
    get_provider_vacations_as_message,
    get_provider_weekly_days_off_as_message,
)
from utils.bot.to_async import (
    add_a_day_off,
    cancel_a_break,
    get_available_break_hours,
    get_provider,
    get_provider_days_off,
    get_tz,
    get_upcoming_provider_breaks,
    remove_a_day_off,
    set_break,
    update_provider,
)

provider_breaks_router = Router(name="provider_breaks")


class BreaksStatesGroup(StatesGroup):
    cancel_break = State()
    edit_days_off = State()
    edit_lunch_start = State()
    edit_lunch_end = State()
    set_break_duration = State()
    set_day_off = State()


@provider_breaks_router.message(
    F.text.in_([_("Breaks & days off"), _("Back to breaks & days off")]),
    IsProviderFilter(),
)
async def breaks_and_dayoffs_menu(message: Message, state: FSMContext):
    await state.clear()
    markup = get_provider_breaks_days_off_menu()
    reply_message = ""

    lunch = await get_provider_lunch_as_message(message.from_user.id)
    reply_message += (lunch or _("You have not set lunch hours yet.")) + "\n\n"

    days_off = await get_provider_weekly_days_off_as_message(message.from_user.id)
    reply_message += (days_off or _("You have not set your weekly days off yet.")) + "\n\n"

    breaks = await get_provider_breaks_as_message(message.from_user.id)
    if breaks:
        reply_message += breaks + "\n\n"

    vacations = await get_provider_vacations_as_message(message.from_user.id)
    if vacations:
        reply_message += vacations

    await message.answer(reply_message, reply_markup=markup)


@provider_breaks_router.message(
    F.text.in_([_("Recurring schedule settings"), _("Back to recurring schedule settings")]),
    IsProviderFilter(),
)
async def recurring_schedule_menu(message: Message, state: FSMContext):
    await state.clear()
    markup = get_provider_recurring_schedule_menu()

    lunch = await get_provider_lunch_as_message(message.from_user.id)
    reply_message = lunch + "\n\n"

    days_off = await get_provider_weekly_days_off_as_message(message.from_user.id)
    reply_message += days_off

    await message.answer(reply_message, reply_markup=markup)


@provider_breaks_router.message(F.text.in_([_("Edit lunch time")]), IsProviderFilter())
async def edit_lunch_start(message: Message, state: FSMContext):
    markup = ReplyKeyboardMarkup(keyboard=[[]], resize_keyboard=True)
    markup.keyboard.append([_("Back to recurring schedule settings")])
    await state.set_state(BreaksStatesGroup.edit_lunch_start)
    reply_message = (
        _("Enter the desirable lunch start time")
        + "\n"
        + _("Please, consider keeping minutes divisible by 15, i.e.: 11:30, 12:45, 13:00")
    )
    await message.answer(reply_message, reply_markup=markup)


@provider_breaks_router.message(BreaksStatesGroup.edit_lunch_start, IsProviderFilter())
async def edit_lunch_end(message: Message, state: FSMContext):
    h, m = message.text.split(":")

    if (not 0 <= int(h) <= 23) or (m not in ["00", "15", "30", "45"]):
        markup = ReplyKeyboardMarkup(keyboard=[[]], resize_keyboard=True)
        markup.keyboard.append([_("Back to recurring schedule settings")])
        await message.answer(
            _("Please, enter time in HH:MM format with MM being among 00, 15, 30, 45."),
            reply_markup=markup,
        )
        return

    start = datetime.strptime(message.text, TIME_INPUT_FORMAT)
    await state.update_data(start=start, start_str=message.text)
    await state.set_state(BreaksStatesGroup.edit_lunch_end)
    markup = ReplyKeyboardMarkup(keyboard=[[]], resize_keyboard=True)
    markup.keyboard.append([_("Back to recurring schedule settings")])
    await message.answer(
        _("Please, enter the desirable lunch end in the same HH:MM format."),
        reply_markup=markup,
    )


@provider_breaks_router.message(BreaksStatesGroup.edit_lunch_end, IsProviderFilter())
async def finish_edit_lunch(message: Message, state: FSMContext):
    state_data = await state.get_data()
    start = state_data["start"]
    h, m = message.text.split(":")
    end = datetime.strptime(message.text, TIME_INPUT_FORMAT)
    if (not 0 <= int(h) <= 23) or (m not in ["00", "15", "30", "45"]) or (start >= end):
        markup = ReplyKeyboardMarkup(keyboard=[[]], resize_keyboard=True)
        markup.keyboard.append([_("Back to recurring schedule settings")])
        await message.answer(
            _("Please, enter end time (bigger than the start time) in HH:MM format with MM among 00, 15, 30, 45."),
            reply_markup=markup,
        )
        return
    await update_provider(message.from_user.id, lunch_start=start, lunch_end=end)
    markup = ReplyKeyboardMarkup(keyboard=[[]], resize_keyboard=True)
    markup.keyboard.append([_("Back to recurring schedule settings")])
    reply_message = _("You've set your recurring lunch time to ") + state_data["start_str"] + " - " + message.text + "."
    await state.clear()
    await message.answer(reply_message, reply_markup=markup)


@provider_breaks_router.message(
    or_f(F.text.in_([_("Edit days off")]), BreaksStatesGroup.edit_days_off), IsProviderFilter()
)
async def finish_edit_days_off(message: Message, state: FSMContext):
    days_off = await get_provider_days_off(message.from_user.id)
    reply_message = ""
    if message.text.split(" ")[0] == "❌":
        days_off.replace(str(WDS_REV[message.text.split(" ")[1]]), "")
        await update_provider(message.from_user.id, days_off="".join(sorted(days_off)))

    elif message.text.split(" ")[0] == "✅":
        days_off += str(WDS_REV[message.text.split(" ")[1]])
        await update_provider(message.from_user.id, days_off="".join(sorted(days_off)))

    elif message.text == _("Yes"):
        pass

    elif message.text == _("No"):
        await state.clear()
        await message.answer(
            _("Recurring schedule menu"),
            reply_markup=await get_provider_recurring_schedule_menu(),
        )

    else:
        if await state.get_state():
            reply_message += _("You've entered something wrong. Please, try again.") + "\n"

    markup = ReplyKeyboardMarkup(keyboard=[[]], resize_keyboard=True)

    for i in range(7):
        if str(i) in days_off:
            emoji = "❌"
        else:
            emoji = "✅"
        markup.keyboard.append([KeyboardButton(text=f"{emoji} {_(WDS[i])}")])

    markup.keyboard.append([_("Back to recurring schedule settings")])
    reply_message += _("Switch ✅(working day) / ❌(day off).")
    await state.set_state(BreaksStatesGroup.edit_days_off)
    await message.answer(reply_message, reply_markup=markup)


@provider_breaks_router.message(F.text.in_([_("Breaks"), _("Back to breaks")]), IsProviderFilter())
async def breaks_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(_("Breaks menu:"), reply_markup=get_provider_breaks_menu())


@provider_breaks_router.message(F.text.in_([_("Set a break")]), IsProviderFilter())
async def set_a_break_duration(message: Message, state: FSMContext):
    await state.set_state(BreaksStatesGroup.set_break_duration)
    markup = get_duration_choices_keyboard()
    markup.keyboard.append([_("Back to breaks")])
    await message.answer(
        _("Choose an option or enter the duration of a break in minutes (should be divisible by 15)."),
        reply_markup=markup,
    )


@provider_breaks_router.message(BreaksStatesGroup.set_break_duration, IsProviderFilter())
async def set_a_break_time(message: Message, state: FSMContext):
    state_data = await state.get_data()
    offset = int(state_data.get("offset") or 0)

    if message.text == _("Next day"):
        offset = offset + 1
        await state.update_data(offset=offset)

    elif message.text == _("Today"):
        offset = 0
        await state.update_data(offset=offset)

    elif message.text == _("Previous day"):
        offset = offset - 1
        await state.update_data(offset=offset)

    elif message.text == _("Cancel"):
        await state.clear()
        await message.answer(_("Breaks menu:"), reply_markup=get_provider_breaks_menu())
        return

    elif message.text.split(" ")[0] == "🕑":
        day: date = state_data["day"]
        provider = await get_provider(message.from_user.id)
        time_string = message.text.split(" ")[1]
        duration = state_data["duration"]
        tz = await get_tz(message.from_user.id)
        start = datetime.combine(day, datetime.strptime(time_string, TIME_INPUT_FORMAT).time(), tzinfo=tz)
        _break = await set_break(provider=provider, start=start, duration=duration)
        await state.clear()
        weekday = _(WEEKDAYS[day.weekday()])
        message_list = [
            _("You have set a break:"),
            weekday + ", " + day.strftime(DATE_FORMAT) + ", " + _break.start.strftime(TIME_FORMAT),
        ]
        markup = await get_main_menu(message.from_user.id)
        await message.answer(
            "\n".join(message_list),
            reply_markup=markup,
        )
        return

    else:
        if int(message.text) > 360:
            markup = get_duration_choices_keyboard()
            markup.keyboard.append([_("Back to breaks")])
            await message.answer(
                _("Choose an option or enter the duration of a break in minutes (should be divisible by 15).")
                + "\n"
                + _("Max break duration is 4h (360 min). If you need more - consider using a few breaks in a row."),
                reply_markup=markup,
            )
            return

    if not state_data.get("duration"):
        try:
            duration = int(message.text)

            if duration % 15 != 0:
                while (duration % 15) != 0:
                    duration += 1

            await state.update_data(duration=duration)

        except ValueError:
            await state.clear()
            markup = get_provider_breaks_menu()
            await message.answer(
                _("You've entered something wrong. Please, try again."),
                reply_markup=markup,
            )
            return

    else:
        duration = state_data["duration"]

    day, available_slots, _is_weekend, _is_vacation = await get_available_break_hours(
        message.from_user.id, duration, offset=offset
    )
    await state.update_data(day=day)
    markup = ReplyKeyboardMarkup(keyboard=[[]], resize_keyboard=True, one_time_keyboard=True)
    row = [_("Previous day")]
    if offset != 0:
        row.append(_("Today"))
    row.append(_("Next day"))
    markup.keyboard.append(row)

    day_string = _(WEEKDAYS[day.weekday()]) + ", " + day.strftime(DATE_FORMAT)

    if _is_vacation:
        reply_message = day_string + "\n" + _("You have a vacation.")
    elif _is_weekend:
        reply_message = day_string + "\n" + _("You have a day-off.")

    elif not available_slots:
        reply_message = day_string + "\n" + _("There is no available slot on this day.")
        markup.keyboard.append([_("See schedule")])
    else:
        for slot in available_slots:
            time_string = slot.strftime(TIME_FORMAT)
            button = KeyboardButton(text=f"🕑 {time_string}")
            markup.keyboard.append([button])
        reply_message = day_string + "\n" + _("Please, select the desirable date and time of the break.")

    markup.keyboard.append([_("Cancel")])
    await message.answer(reply_message, reply_markup=markup)


@provider_breaks_router.message(
    F.text.in_([_("Cancel a break")]),
    IsProviderFilter(),
)
async def cancel_break(message: Message, state: FSMContext):
    await state.set_state(BreaksStatesGroup.cancel_break)
    markup = ReplyKeyboardMarkup(keyboard=[[]], resize_keyboard=True, one_time_keyboard=True)
    reply_message = ""

    if message.text.split(" ")[0] == "❌":
        break_id = message.text.split("#")[1]
        await cancel_a_break(message.from_user.id, break_id)
        reply_message += _("Break") + " (" + message.text.split(" ", 1)[1] + ") " + _("was canceled.") + "\n"
        markup = get_provider_breaks_days_off_menu()
        await message.answer(reply_message, reply_markup=markup)
        return

    breaks = await get_upcoming_provider_breaks(message.from_user.id)

    for _break in breaks:
        start = _break["start"]
        message_list = [
            "❌",
            _(WDS[start.date().weekday()]),
            start.strftime(DATE_FORMAT),
            start.strftime(TIME_FORMAT),
            f"#{_break['id']}",
        ]
        markup.keyboard.append([KeyboardButton(text=" ".join(message_list))])

    if not breaks:
        reply_message += _("You don't have any breaks planned")
    elif message.text.split(" ")[0] == "❌":
        reply_message += _("Do you want to cancel another break?")
    else:
        reply_message += _("Do you want to cancel a break?")

    markup.keyboard.append([_("Back to breaks")])
    await message.answer(reply_message, reply_markup=markup)


@provider_breaks_router.message(
    or_f(F.text.in_([_("Days off"), _("Back to days off")]), BreaksStatesGroup.set_day_off), IsProviderFilter()
)
async def edit_days_off(message: Message, state: FSMContext):
    markup = ReplyKeyboardMarkup(keyboard=[[]], resize_keyboard=True)
    offset = (await state.get_data()).get("offset", 0)
    provider = await get_provider(message.from_user.id)
    message_start = ""
    if message.text[0] in {"📝", "📅", "🏖", "🏠"}:
        date_str = message.text.split(
            " ",
        )[2]
        if message.text[0] == "📝":
            message_start = _("You have reservations on this date. Cancel them before planning a vacation") + "\n\n"
        elif message.text[0] == "📅":
            day = datetime.strptime(date_str, DATE_FORMAT)
            await add_a_day_off(provider, day.date())
            message_start = _("You have added the day off for ") + date_str + "\n\n"
        elif message.text[0] == "🏖":
            day = datetime.strptime(date_str, DATE_FORMAT)
            await remove_a_day_off(provider, day.date())
            message_start = _("You have removed the day off for ") + date_str + "\n\n"
        elif message.text[0] == "🏠":
            message_start = date_str + _(" is already a weekend. No need to set a day off.\n\n")
    else:
        await state.set_state(BreaksStatesGroup.set_day_off)

    week = await get_provider_week_overview(provider, offset)
    for day in week:
        _date = day["date"]
        message_list = [day["emoji"], _(WDS[_date.weekday()]), day["date"].strftime(DATE_FORMAT)]
        markup.keyboard.append([KeyboardButton(text=" ".join(message_list))])

    markup.keyboard.append([_("Back to breaks & days off")])
    instructions = (
        _("Switch available weekdays (📅) to days off (🏖).")
        + "\n"
        + _("You cannot set a day off for a day with scheduled reservations (📝).")
        + "\n"
        + _("There is no need to set a day off on your recurring weekend (🏠).")
    )
    await message.answer(
        message_start + instructions,
        reply_markup=markup,
    )
