from datetime import date, datetime, time, timedelta
from typing import Any

from django.db.models import F, Q

from apps.roles.models import Provider, User
from apps.scheduler.models import Break, Reservation, Vacation
from utils.db import normalize_time


def get_events_by_day(
    day: date,
    day_start: datetime,
    day_end: datetime,
    provider: Provider = None,
    client: User = None,
) -> list:
    qs = Reservation.objects.select_related("provider", "client", "service").filter(
        Q(start__lte=day_end) & Q(end__gte=day_start),
        is_canceled=False,
    )
    provider_res = qs.filter(provider=provider) if provider else Reservation.objects.none()
    client_res = qs.filter(client=client) if client else Reservation.objects.none()
    reservations = [
        item
        for item in (provider_res | client_res)
        .annotate(
            provider_name=F("provider__user__full_name"),
            client_name=F("client__full_name"),
            client_username=F("client__tg_username"),
            client_phone=F("client__phone"),
            service_name=F("service__name"),
        )
        .distinct()
        .values()
    ]

    breaks = [item for item in Break.objects.filter(provider=provider, start__date=day, end__date=day).values()]

    reserved_unsorted = reservations + breaks
    if provider.lunch_start and provider.lunch_end:
        lunch = {
            "start": datetime.combine(date=day, time=provider.lunch_start, tzinfo=provider.user.tz).astimezone(
                tz=day_start.tzinfo
            ),
            "end": datetime.combine(date=day, time=provider.lunch_end, tzinfo=provider.user.tz).astimezone(
                tz=day_start.tzinfo
            ),
            "is_lunch": True,
        }
        reserved_unsorted.append(lunch)

    return sorted(reserved_unsorted, key=lambda d: d["start"])


def is_vacation(tg_id: int, day: date) -> bool:
    provider = User.objects.filter(tg_id=tg_id).first().provider
    return Vacation.objects.filter(provider=provider, start_date__lte=day, end_date__gte=day).exists()


def find_available_slots(
    current_user: User,
    provider: Provider,
    day: date,
    client: User = None,
    event_duration: int = 15,
) -> tuple[list[datetime], bool, bool]:
    tz = current_user.tz
    now = datetime.now(tz=tz)

    day_start = datetime.combine(day, time(hour=0, minute=0), tzinfo=tz) if day != now.date() else normalize_time(now)
    day_end = datetime.combine(day, time(hour=0, minute=0), tzinfo=tz)
    if day_end.astimezone(tz=provider.user.tz).date() <= day_start.astimezone(tz=provider.user.tz).date():
        day_end = day_end + timedelta(days=1)

    events = get_events_by_day(day=day, day_start=day_start, day_end=day_end, provider=provider, client=client)
    duration = timedelta(minutes=event_duration)
    slot_duration = timedelta(minutes=provider.slot)
    weekend = get_weekend(provider)

    available_slots = []
    cursor = day_start

    for event in events:
        event_start = event["start"]
        event_end = event["end"]

        while event_start - cursor >= duration:
            provider_start = cursor.astimezone(tz=provider.user.tz).time()
            provider_end = (cursor + duration).astimezone(tz=provider.user.tz).time()

            if not (
                cursor.astimezone(tz=provider.user.tz).weekday() in weekend
                or is_vacation(provider.user.tg_id, cursor.astimezone(tz=provider.user.tz).date())
                or not (provider.start <= provider_start <= provider_end <= provider.end)
            ):
                available_slots.append(cursor.astimezone(tz=tz))
            cursor += slot_duration
        cursor = event_end

    while cursor <= (day_end - duration):
        provider_start = cursor.astimezone(tz=provider.user.tz).time()
        provider_end = (cursor + duration).astimezone(tz=provider.user.tz).time()

        if not (
            cursor.astimezone(tz=provider.user.tz).weekday() in weekend
            or is_vacation(provider.user.tg_id, cursor.astimezone(tz=provider.user.tz).date())
            or not (provider.start <= provider_start <= provider_end <= provider.end)
        ):
            available_slots.append(cursor.astimezone(tz=tz))
        cursor += slot_duration

    _is_day_off = day.weekday() in get_weekend(provider)
    _is_vacation = is_vacation(provider.user.tg_id, day)

    return available_slots, _is_day_off, _is_vacation


def get_weekend(provider: Provider) -> list[int]:
    weekend = sorted([int(i) for i in provider.weekend])
    return weekend


async def get_provider_week_overview(provider: Provider, offset: int = 0) -> list[dict[str, Any]]:
    today = datetime.now(tz=provider.user.tz).date()
    start_date = today + timedelta(days=offset)
    end_date = start_date + timedelta(days=6)  # 7 days total, including start_date

    # Get all reservations in the date range
    reservations = (
        Reservation.objects.filter(provider=provider, start__date__gte=start_date, start__date__lte=end_date)
        .values("start__date")
        .distinct()
    )

    # Get all vacations in the date range
    vacations = Vacation.objects.filter(
        start_date__lte=end_date,
        end_date__gte=start_date,
        provider=provider,
    ).values("start_date", "end_date")

    # Create a set of dates with reservations for faster lookup
    reservation_dates = set(reservation["start__date"] for reservation in reservations)

    # Create a set of vacation dates for faster lookup
    vacation_dates = set()

    for vacation in vacations:
        current_date = max(vacation["start_date"], start_date)
        while vacation["start_date"] <= current_date <= vacation["end_date"]:
            vacation_dates.add(current_date)
            current_date += timedelta(days=1)

    # Generate the result list
    result = []
    days_off = get_weekend(provider)
    for i in range(7):
        current_date = start_date + timedelta(days=i)
        if current_date in reservation_dates:
            emoji = "📝"
        elif current_date.weekday() in days_off:
            emoji = "🏠"
        elif current_date in vacation_dates:
            emoji = "🏖"
        else:
            emoji = "📅"

        result.append(
            {
                "date": current_date,
                "emoji": emoji,
            }
        )

    return result
