from bot import _
from moneyed import format_money
from utils.bot.consts import DATE_FORMAT, DATE_TIME_FORMAT, TIME_FORMAT, WDS, WEEKDAYS
from utils.bot.to_async import (
    count_client_reservations_by_pk,
    get_client_reservations,
    get_provider_clients,
    get_provider_data,
    get_provider_events_by_offset,
    get_provider_services,
    get_tz,
    get_upcoming_provider_breaks,
    get_upcoming_provider_vacations,
    get_user,
    is_provider,
    is_vacation,
    is_weekend,
    last_client_reservation,
    next_client_reservation,
)


async def get_provider_services_as_message(tg_id: int) -> str:
    services = await get_provider_services(tg_id)
    reply_message_list = []
    if services:
        for service in services:
            price = format_money(service.price, locale=(await get_user(tg_id)).locale)
            to_message: str = service.name + "\n" + str(service.duration) + " " + _("minutes\n") + price + "\n"
            if await is_provider(tg_id) and not service.is_active:
                to_message += _("(inactive)") + "\n"
            reply_message_list.append(to_message)
        return "\n".join(reply_message_list)
    else:
        return ""


async def get_client_reservations_as_message(tg_id: int, is_past: bool = False) -> str:
    tz = await get_tz(tg_id)
    reservations = await get_client_reservations(tg_id, is_past=is_past)
    if not is_past:
        reply_no = _("You have no upcoming reservations.")
    else:
        reply_no = _("You have no past reservations.")
    if reservations:
        answer_message_list = []
        for reservation in reservations:
            weekday = reservation["start"].astimezone(tz).strftime("%A")
            start_datetime = reservation["start"].astimezone(tz).strftime(DATE_TIME_FORMAT)
            service = reservation["service_name"]
            name = reservation["full_name"]
            username = reservation["tg_username"]
            answer_message_list.append(
                _(weekday)
                + ", "
                + start_datetime
                + "\n\n"
                + _("Service: {service}\n").format(service=service)
                + _("Provider: {name}, @{username}\n").format(name=name, username=username)
                + reservation["phone"]
                + "\n"
            )
        return "\n\n".join(answer_message_list)
    else:
        return reply_no


async def get_provider_clients_as_message(tg_id: id) -> str:
    tz = await get_tz(tg_id)
    clients = await get_provider_clients(tg_id)
    if clients:
        answer_message_list = []
        for client in clients:
            username = ("📱 @" + client.tg_username + "\n") if client.tg_username else ""
            phone = ("☎️ " + client.phone) if client.phone else ""
            (past_reservations_count, upcoming_reservations_count) = await count_client_reservations_by_pk(
                tg_id, client.pk
            )
            last_reservation = await last_client_reservation(client.pk)
            last_reservation_str = (
                (last_reservation.start.astimezone(tz).strftime(DATE_TIME_FORMAT)) if last_reservation else "-\n"
            )
            next_reservation = await next_client_reservation(client.pk)
            next_reservation_str = (
                (next_reservation.start.astimezone(tz).strftime(DATE_TIME_FORMAT)) if next_reservation else "-\n"
            )
            answer_message_list.append(
                "👤 "
                + client.full_name
                + "\n"
                + username
                + phone
                + "\n⏪ "
                + _("Past reservations: ")
                + str(past_reservations_count)
                + "\n⏩ "
                + _("Upcoming reservations: ")
                + str(upcoming_reservations_count)
                + "\n⏮ "
                + _("Last reservation: ")
                + last_reservation_str
                + "\n⏭ "
                + _("Next reservation: ")
                + next_reservation_str
            )

        return "\n***\n\n".join(answer_message_list)
    else:
        return _("You have had no clients yet.")


async def get_provider_events_as_message(tg_id: int, offset: int) -> str:
    tz = await get_tz(tg_id)
    day, events = await get_provider_events_by_offset(tg_id, offset)
    events_list = ["🗓 <b>" + (_(day.strftime("%A")) + ", " + day.strftime(DATE_FORMAT) + "</b>")]

    if not events:
        events_list.append(_("No appointments."))

    for event in events:
        time = f'⌚️ {event["start"].astimezone(tz).strftime(TIME_FORMAT)} - {event["end"].astimezone(tz).strftime(TIME_FORMAT)}\n'
        _is_weekend = await is_weekend(tg_id, day)
        _is_vacation = await is_vacation(tg_id, day)
        if _is_weekend:
            events_list.append(_("You have a day-off."))
        elif _is_vacation:
            events_list.append(_("You have a vacation."))
        else:
            if "client_name" in event:
                service = event["service_name"] + "\n"
                name = "👤 " + event["client_name"] + "\n"
                username = (", @" + event["client_username"] + "\n") if event.get("client_username") else ""
                phone = ("☎️ " + event["client_phone"] + "\n") if event.get("client_phone") else ""
                events_list.append(time + "📝 " + service + name + username + phone)
            elif event.get("is_lunch", False):
                pass
            else:
                events_list.append(time + "⏳ " + _("Break") + "\n")  # TODO: add break description field
    return "\n\n".join(events_list)


async def get_provider_breaks_as_message(tg_id: int) -> str:
    breaks = await get_upcoming_provider_breaks(tg_id)
    tz = await get_tz(tg_id)
    if breaks:
        breaks_list = ["⏳ <b>" + _("Upcoming breaks:") + "</b>\n"]
        for brk in breaks:
            date_dud = "date"
            breaks_list.append(
                _(WEEKDAYS[brk[date_dud].weekday()])
                + ", "
                + brk["date"].strftime(DATE_FORMAT)
                + ", "
                + brk["start"].astimezone(tz).strftime(TIME_FORMAT)
                + " - "
                + brk["end"].astimezone(tz).strftime(TIME_FORMAT)
            )

        return "\n".join(breaks_list)
    else:
        return "⏳ <b>" + _("You have no upcoming breaks.") + "</b>\n"


async def get_provider_vacations_as_message(tg_id: int) -> str:
    vacations = await get_upcoming_provider_vacations(tg_id)
    if vacations:
        vacations_list = ["🏖 <b>" + _("Upcoming vacations:") + "</b>\n"]

        for vacation in vacations:
            start_weekday = vacation["start_date"].strftime("%A")
            start_weekday_str = _(start_weekday)
            start = vacation["start_date"].strftime(DATE_FORMAT)
            end_weekday = vacation["end_date"].strftime("%A")
            end_weekday_str = _(end_weekday)
            end = vacation["end_date"].strftime(DATE_FORMAT)
            vacations_list.append(start_weekday_str + ", " + start + " - " + end_weekday_str + ", " + end + "\n")

        return "\n".join(vacations_list)

    else:
        return "🏖 <b>" + _("You have no upcoming vacations.") + "</b>\n"


async def get_provider_lunch_as_message(tg_id: int) -> str | None:
    provider_data = await get_provider_data(tg_id)
    if provider_data.get("lunch_start") and provider_data.get("lunch_end"):
        return (
            "🍴 <b>"
            + _("Lunch: ")
            + "</b>"
            + provider_data["lunch_start"].strftime(TIME_FORMAT)
            + " - "
            + provider_data["lunch_end"].strftime(TIME_FORMAT)
        )
    else:
        return "🍴 <b>" + _("You have not set lunch hours yet.") + "</b>"


async def get_provider_weekly_days_off_as_message(tg_id: int) -> str | None:
    provider_data = await get_provider_data(tg_id)
    if provider_data.get("weekend"):
        days_off_list = [i for i in provider_data["weekend"]]
        return "⛔️ <b>" + _("Days off: ") + "</b>" + ", ".join([WDS[int(day)] for day in days_off_list])
    else:
        return "⛔️ <b>" + _("You have not set your weekly days off yet.") + "</b>"
