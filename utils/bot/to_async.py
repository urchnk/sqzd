import random
import string
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Any, Union

from django.db.models import F, Q, QuerySet
from django.forms import model_to_dict
from django.utils import timezone

from apps.roles.models import Provider, User
from apps.scheduler.models import Break, Reservation, Vacation
from apps.scheduler.services import find_available_slots, get_events_by_day
from apps.services.models import Service
from asgiref.sync import sync_to_async


def get_random_username():
    symbols = string.ascii_letters + string.digits
    return "".join(random.choice(symbols) for _ in range(7))


@sync_to_async
def get_user(tg_id: int = None, user_id: int = None, username: str = None, phone: str = None) -> User | None:
    user = None
    if tg_id:
        user = User.objects.filter(tg_id=tg_id).first()
    if user_id:
        user = User.objects.filter(id=user_id).first()
    if username:
        user = User.objects.filter(username=username).first()
    if phone:
        user = User.objects.filter(phone=phone).first()
    return user


@sync_to_async
def get_or_create_user(
    first_name: str,
    last_name: str = None,
    tg_id: int = None,
    phone: str = None,
    username: str = None,
    locale: str = "uk",
) -> User:
    if tg_id:
        user = User.objects.filter(tg_id=tg_id).first()
        if user:
            return user
        else:
            user = User(
                tg_id=tg_id,
                username=username or (first_name + get_random_username()),
                tg_username=username,
                locale=locale,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
            )
            user.save()
            return user


@sync_to_async
def create_user(first_name: str, last_name: str, phone: int, tg_id: int = None) -> User:
    random_username = first_name + get_random_username()
    while User.objects.filter(username=random_username).exists():
        random_username = first_name + get_random_username()
    user = User(
        username=random_username,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        tg_id=tg_id,
    )
    user.save()
    return user


@sync_to_async
def check_user_exists(username: str = None, phone: str = None) -> bool:
    return User.objects.filter(Q(username=username) | Q(tg_username=username) | Q(phone=phone)).exists()


@sync_to_async
def update_user(tg_id: int, **kwargs) -> User | None:
    user = User.objects.filter(tg_id=tg_id).first()
    for key, value in kwargs.items():
        setattr(user, key, value)
    user.save()
    return user


@sync_to_async
def count_all_users() -> int:
    total = User.objects.all(is_active=True).count()
    return total


@sync_to_async
def get_provider(tg_id: int) -> Provider | None:
    user = User.objects.filter(tg_id=tg_id).first()
    if user:
        provider = Provider.objects.filter(user=user).first()
        return provider
    else:
        return None


@sync_to_async
def get_provider_data(tg_id: int) -> dict | None:
    user = User.objects.filter(tg_id=tg_id).first()
    if user:
        provider = Provider.objects.filter(user=user).first()
        data = model_to_dict(provider) if provider else None
        return data
    else:
        return None


@sync_to_async
def get_provider_days_off(tg_id: int) -> str:
    provider: Provider = User.objects.filter(tg_id=tg_id).first().provider
    return provider.weekend


@sync_to_async
def add_provider_to_user(
    tg_id: int,
    email: str = None,
    phone: str = None,
    start: time = None,
    end: time = None,
) -> Provider:
    user = User.objects.filter(tg_id=tg_id).first()
    provider = Provider.objects.create(user=user, email=email, phone=phone, start=start, end=end)
    return provider


@sync_to_async
def is_provider(tg_id: int) -> bool:
    user = User.objects.filter(tg_id=tg_id).first()
    return True if (user and user.is_provider()) else False


@sync_to_async
def update_provider(tg_id: int, **kwargs) -> Provider:
    provider: Provider = User.objects.filter(tg_id=tg_id).first().provider
    for k, v in kwargs.items():
        setattr(provider, k, v)
    provider.save()

    return provider


@sync_to_async
def add_service(name: str, duration: int, price: Decimal, tg_id: int) -> Service:
    provider: Provider = User.objects.filter(tg_id=tg_id).first().provider
    new_service: Service = Service(name=name, price=price, duration=duration)
    new_service.save()
    new_service.providers.add(provider)
    return new_service


@sync_to_async
def check_service_exists(name: str, tg_id: int) -> bool:
    provider: Provider = User.objects.filter(tg_id=tg_id).first().provider
    return Service.objects.filter(name=name, providers=provider).exists()


@sync_to_async
def get_service_data(name: str, tg_id: int) -> dict | None:
    provider: Provider = User.objects.filter(tg_id=tg_id).first().provider
    service = Service.objects.filter(name=name, providers=provider).first()
    data = model_to_dict(service) if service else None
    return data


@sync_to_async
def count_upcoming_service_reservations(service_id: int) -> int:
    now = timezone.make_aware(datetime.now(), timezone.get_current_timezone())
    count = Reservation.objects.select_related("service").filter(service__pk=service_id, end__gt=now).count()
    return count


@sync_to_async
def count_past_service_reservations(service_id: int) -> int:
    now = timezone.make_aware(datetime.now(), timezone.get_current_timezone())
    count = Reservation.objects.select_related("service").filter(service__pk=service_id, start__lt=now).count()
    return count


@sync_to_async
def count_client_reservations_by_pk(provider_id: int, client_pk: int) -> tuple[int, int]:
    now = timezone.make_aware(datetime.now(), timezone.get_current_timezone())
    past: int = (
        Reservation.objects.select_related("service", "provider")
        .filter(
            client__pk=client_pk,
            provider__user__tg_id=provider_id,
            start__lt=now,
        )
        .count()
    )
    upcoming: int = (
        Reservation.objects.select_related("service")
        .filter(
            client__pk=client_pk,
            provider__user__tg_id=provider_id,
            start__gt=now,
        )
        .count()
    )
    return past, upcoming


async def last_client_reservation(client_pk: int) -> Reservation | None:
    now = timezone.make_aware(datetime.now(), timezone.get_current_timezone())
    return (
        Reservation.objects.select_related("client")
        .filter(client__pk=client_pk, start__lt=now)
        .order_by("start")
        .last()
    )


async def next_client_reservation(client_pk: int) -> Reservation | None:
    now = timezone.make_aware(datetime.now(), timezone.get_current_timezone())
    return (
        Reservation.objects.select_related("client")
        .filter(client__pk=client_pk, start__gt=now)
        .order_by("start")
        .first()
    )


@sync_to_async
def count_past_client_reservations(provider_id: int, client_id: int) -> int:
    now = timezone.make_aware(datetime.now(), timezone.get_current_timezone())
    count = (
        Reservation.objects.select_related("service")
        .filter(
            client__tg_id=client_id,
            provider__tg_id=provider_id,
            start__lt=now,
        )
        .count()
    )
    return count


@sync_to_async
def get_provider_services(tg_id: int, is_active: bool = True) -> Union[QuerySet, list[Service]] | None:
    provider: Provider = User.objects.filter(tg_id=tg_id).first().provider
    services = Service.objects.filter(providers=provider, is_active=is_active)
    return services


@sync_to_async
def update_service(pk: int, **kwargs):
    service = Service.objects.filter(pk=pk).first()
    for key, value in kwargs.items():
        setattr(service, key, value)
    service.save()
    return service


@sync_to_async
def remove_service(pk: int):
    service = Service.objects.filter(pk=pk).first()
    service.delete()


@sync_to_async
def get_provider_clients(tg_id: int, order_by: str = "client__full_name") -> Union[QuerySet, list[User]] | None:
    provider: Provider = User.objects.filter(tg_id=tg_id).first().provider
    reservations_clients_ids = (
        Reservation.objects.filter(provider=provider).values_list("client", flat=True).distinct().order_by(order_by)
    )
    clients = User.objects.filter(pk__in=reservations_clients_ids)
    return clients if clients else None


@sync_to_async
def get_provider_reservations_by_date(tg_id: int, day: date) -> Union[QuerySet, list[Reservation]] | None:
    provider: Provider = User.objects.filter(tg_id=tg_id).first().provider
    return Reservation.objects.filter(provider=provider, date=day, is_canceled=False).values()


@sync_to_async
def is_vacation(tg_id: int, day: date) -> bool:
    provider: Provider = User.objects.filter(tg_id=tg_id).first().provider
    return Vacation.objects.filter(provider=provider, start_date__lte=day, end_date__gte=day).exists()


@sync_to_async
def is_day_off(tg_id: int, day: date) -> bool:
    provider: Provider = User.objects.filter(tg_id=tg_id).first().provider
    return str(day.weekday()) in provider.weekend


@sync_to_async
def get_provider_breaks_by_date(tg_id: int, day: date) -> Union[QuerySet, list[Break]] | None:
    provider: Provider = User.objects.filter(tg_id=tg_id).first().provider
    return Break.objects.filter(provider=provider, date=day)


@sync_to_async
def get_upcoming_provider_breaks(
    tg_id: int,
) -> Union[QuerySet, list[Break]] | None:
    provider: Provider = User.objects.filter(tg_id=tg_id).first().provider
    now = timezone.make_aware(datetime.now(), timezone.get_current_timezone())
    breaks = Break.objects.filter(provider=provider, end__gte=now)
    return breaks.values()


@sync_to_async
def get_upcoming_provider_vacations(
    tg_id: int,
) -> Union[QuerySet, list[Vacation]] | None:
    provider: Provider = User.objects.filter(tg_id=tg_id).first().provider
    now = timezone.make_aware(datetime.now(), timezone.get_current_timezone())
    return Vacation.objects.filter(provider=provider, end_date__gte=now.date()).values()


@sync_to_async
def get_available_hours(
    tg_id: int, service_name: str, client_id: int = None, client_tg_id: int = None, offset: int = 0
) -> Any:
    provider: Provider = User.objects.filter(tg_id=tg_id).first().provider
    service: Service = Service.objects.filter(name=service_name, providers=provider).first()
    if client_id:
        client = User.objects.filter(pk=client_id).first()
    elif client_tg_id:
        client = User.objects.filter(tg_id=client_tg_id).first()
    else:
        raise ValueError
    day = date.today() + timedelta(days=offset)

    available_slots, _is_day_off, _is_vacation = find_available_slots(
        provider=provider, client=client, event_duration=service.duration, day=day
    )
    return day, available_slots, _is_day_off, _is_vacation


@sync_to_async
def get_available_break_hours(tg_id: int, duration: int, offset: int = 0):
    provider: Provider = User.objects.filter(tg_id=tg_id).first().provider
    day: date = date.today() + timedelta(days=offset)
    available_slots = find_available_slots(provider=provider, event_duration=duration, day=day)
    return day, available_slots


@sync_to_async
def get_provider_events_by_offset(tg_id: int, offset: int = 0) -> Any:
    provider: Provider = User.objects.filter(tg_id=tg_id).first().provider
    to_tz = timezone.get_current_timezone()  # TODO: handle timezones
    day = timezone.make_aware(datetime.now(), to_tz).date() + timedelta(days=offset)
    events = get_events_by_day(provider=provider, day=day)

    return day, events


@sync_to_async
def set_reservation(client: User, provider: Provider, service_id: int, start: datetime) -> Reservation:
    service = Service.objects.filter(pk=service_id).first()
    end = start + timedelta(minutes=service.duration)
    new_reservation = Reservation(
        client=client,
        provider=provider,
        service=service,
        price=service.price,
        start=start,
        end=end,
    ).save()
    return new_reservation


@sync_to_async
def set_break(provider: Provider, start: datetime, duration: int) -> Break:
    end = start + timedelta(minutes=duration)
    new_break = Break(provider=provider, start=start, end=end).save()
    return new_break


@sync_to_async
def cancel_a_break(tg_id: int, break_id: int) -> None:
    provider: Provider = User.objects.filter(tg_id=tg_id).first().provider
    break_to_cancel = Break.objects.filter(provider=provider, id=break_id).first()
    if break_to_cancel:
        break_to_cancel.delete()


@sync_to_async
def add_a_day_off(provider: Provider, day: date):
    vacation = Vacation.objects.filter(provider=provider, start_date__lte=day, end_date__gte=day).first()
    new_vacation = None
    if not vacation:
        before = Vacation.objects.filter(provider=provider, end_date=day - timedelta(days=1)).first()
        after = Vacation.objects.filter(provider=provider, start_date=day + timedelta(days=1)).first()
        if before and after:
            before.end_date = after.end_date
            before.save()
            after.delete()
        elif before:
            before.end_date = day
            before.save()
        elif after:
            after.start_date = day
            after.save()
        else:
            new_vacation = Vacation(
                provider=provider,
                start_date=day,
                end_date=day,
            )
            new_vacation.save()

    return vacation or new_vacation


@sync_to_async
def remove_a_day_off(provider: Provider, day: date):
    vacation = Vacation.objects.filter(provider=provider, start_date__lte=day, end_date__gte=day).first()
    new_vacation = None
    if vacation:
        if vacation.start_date == day:
            if vacation.end_date == day:
                vacation.delete()
            else:
                vacation.start_date = day + timedelta(days=1)
                vacation.save()
        elif vacation.end_date == day:
            vacation.end_date = day - timedelta(days=1)
            vacation.save()
        else:
            new_vacation = Vacation(
                provider=provider,
                start_date=(day + timedelta(days=1)),
                end_date=vacation.end_date,
            )
            vacation.end_date = day - timedelta(days=1)
            vacation.save()
            new_vacation.save()
    return new_vacation or vacation


@sync_to_async
def update_reservation(identifier: int, **kwargs) -> Reservation:
    reservation = Reservation.objects.filter(identifier=identifier).first()
    for key, value in kwargs.items():
        setattr(reservation, key, value)
    reservation.save()
    return reservation


@sync_to_async
def get_reservation(identifier: int) -> Reservation:
    reservation = Reservation.objects.filter(identifier=int(identifier)).first()
    return reservation


@sync_to_async
def get_client_reservations(tg_id: int, is_past: bool = False) -> Union[QuerySet, list[Reservation]] | None:
    client = User.objects.filter(tg_id=tg_id).first()
    now = timezone.make_aware(datetime.now(), timezone.get_current_timezone())

    # Both upcoming and past reservations here include an ongoing one if there is such.
    if not is_past:
        base_qs = Reservation.objects.filter(client=client, end__gt=now)
    else:
        base_qs = Reservation.objects.filter(client=client, start__lt=now)

    return (
        base_qs.select_related("provider")
        .annotate(
            tg_username=F("provider__user__tg_username"),
            phone=F("provider__phone"),
            full_name=F("provider__user__full_name"),
        )
        .select_related("service")
        .annotate(service_name=F("service__name"))
        .values()
    )
