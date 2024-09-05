from datetime import datetime, time, timedelta

from django.db import models

from utils.bot.consts import DEFAULT_SLOT


def normalize_duration(value: int, divider: int = DEFAULT_SLOT) -> int:
    if (value % divider) != 0:
        while (value % divider) != 0:
            value += 1
    return value


def normalize_time(value: datetime | time | None) -> datetime | time | None:
    ok = [0, 15, 30, 45]
    if value and value.minute not in ok:
        while value.minute not in ok:
            value += timedelta(minutes=1)
    if type(value) == datetime:
        value = value.replace(second=0, microsecond=0)
    return value


class TimeStampedModelMixin:
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class NormalizedDurationField(models.PositiveIntegerField):
    def pre_save(self, model_instance, add):
        attr = super().pre_save(model_instance, add)
        normalized = normalize_duration(attr)
        setattr(model_instance, self.attname, normalized)
        return normalized


class NormalizedDateTimeField(models.DateTimeField):
    def pre_save(self, model_instance, add):
        attr = super().pre_save(model_instance, add)
        normalized = normalize_time(attr)
        setattr(model_instance, self.attname, normalized)
        return normalized


class NormalizedTimeField(models.TimeField):
    def pre_save(self, model_instance, add):
        attr = super().pre_save(model_instance, add)
        normalized = normalize_time(attr)
        setattr(model_instance, self.attname, normalized)
        return normalized
