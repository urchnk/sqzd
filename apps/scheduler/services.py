from datetime import date, datetime, time, timedelta
from typing import Any

from django.db.models import F, Q

from apps.roles.models import Provider, User
from apps.scheduler.models import Break, Reservation, Vacation


def get_events_by_day(
    current_user: User,
    day: date,
    provider: Provider = None,
    client: User = None,
) -> list:
    now = datetime.now(tz=current_user.tz)
    qs = Reservation.objects.select_related("provider", "client", "service").filter(
        Q(end__date=day) & Q(start__date=day),
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

    breaks = [item for item in Break.objects.filter(provider=provider, date=day, start__gt=now).values()]

    reserved_unsorted = reservations + breaks
    if provider.lunch_start and provider.lunch_end:
        lunch = {
            "start": datetime.combine(date=day, time=provider.lunch_start, tzinfo=provider.user.tz).astimezone(
                tz=current_user.tz
            ),
            "end": datetime.combine(date=day, time=provider.lunch_end, tzinfo=provider.user.tz).astimezone(
                tz=current_user.tz
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
    client_tz: bool = True,
) -> tuple[list[datetime], bool, bool]:
    tz = client.tz if client_tz else provider.user.tz
    now = datetime.now(tz=tz)

    events = get_events_by_day(current_user=current_user, provider=provider, client=client, day=day)
    duration = timedelta(minutes=event_duration)
    slot_duration = timedelta(minutes=provider.slot)

    start_time, end_time = get_start_end(
        current_user=current_user,
        provider=provider,
        day=day,
        now=now,
        duration=duration,
    )

    _is_day_off = day.weekday() in get_weekend(provider)
    _is_vacation = is_vacation(provider.user.tg_id, day)

    available_slots = []

    if not _is_day_off and not _is_vacation and (now < (end_time - duration)):
        cursor = start_time

        for event in events:
            event_start = event["start"].astimezone(tz=current_user.tz)
            event_end = event["end"].astimezone(tz=current_user.tz)

            while event_start - cursor >= duration:
                available_slots.append(cursor)
                cursor += slot_duration
            cursor = event_end

        while cursor <= (end_time - duration):
            available_slots.append(cursor)
            cursor += slot_duration

    return available_slots, _is_day_off, _is_vacation


# def is_day_unavailable(provider: Provider, day: date, now: datetime, duration: int) -> bool:
#     if day.weekday() in get_weekend(provider):
#         return True
#
#     if is_vacation(provider.user.tg_id, day):
#         return True
#
#     end_time = datetime.combine(day, provider.end, tzinfo=provider.user.tz)
#     if day == now.date() and now > (end_time - timedelta(minutes=duration)):
#         return True
#
#     return False


def get_weekend(provider: Provider) -> list[int]:
    weekend = sorted([int(i) for i in provider.weekend])
    return weekend  # TODO: de-hardcode weekends handling (or maybe not?)


def get_start_end(
    current_user: User, provider: Provider, day: date, now: datetime, duration: timedelta
) -> tuple[datetime, datetime]:
    tz = current_user.tz
    start_time = max(
        datetime.combine(day, provider.start, tzinfo=provider.user.tz),
        datetime.combine(day, time(hour=0, minute=0), tzinfo=tz),
    ).astimezone(tz=current_user.tz)

    end_time = min(
        datetime.combine(day, provider.end, tzinfo=provider.user.tz),
        datetime.combine(day + timedelta(days=1), time(hour=0, minute=0), tzinfo=tz),
    ).astimezone(tz=current_user.tz)

    if day == now.date():
        provider_end_time = datetime.combine(day, provider.end, tzinfo=provider.user.tz)
        available_time = provider_end_time - now
        slot_count = int(available_time / duration)
        start_time = max(start_time, provider_end_time - (duration * slot_count))

    return start_time.astimezone(tz=current_user.tz), end_time.astimezone(tz=current_user.tz)


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
