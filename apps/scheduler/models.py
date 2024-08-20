from django.db import models

from apps.roles.models import Provider, User
from apps.services.models import Service
from djmoney.models.fields import MoneyField
from utils.db import NormalizedDateTimeField, TimeStampedModelMixin


class Reservation(models.Model, TimeStampedModelMixin):
    client = models.ForeignKey(
        User,
        verbose_name="Client",
        related_name="reservations",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    provider = models.ForeignKey(
        Provider,
        related_name="reservations",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    service = models.ForeignKey(Service, on_delete=models.CASCADE, null=True, blank=True)
    price = MoneyField(max_digits=14, decimal_places=2, null=True, default_currency="UAH")
    date = models.DateField(null=True, blank=True)
    start = NormalizedDateTimeField(null=True, blank=True)
    end = NormalizedDateTimeField(null=True, blank=True)
    is_canceled = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        self.date = self.start.date()
        if not kwargs.get("end") and kwargs.get("is_break"):
            self.end = kwargs["provider"].break_end
        super(Reservation, self).save(*args, **kwargs)


class Vacation(models.Model, TimeStampedModelMixin):
    provider = models.ForeignKey(
        Provider,
        related_name="vacations",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)


class Break(models.Model, TimeStampedModelMixin):
    provider = models.ForeignKey(
        Provider,
        related_name="breaks",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    date = models.DateField(null=True, blank=True)
    start = NormalizedDateTimeField(null=True, blank=True)
    end = NormalizedDateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        self.date = self.start.date()
        if not kwargs.get("end") and kwargs.get("is_break"):
            self.end = kwargs["provider"].break_end
        super(Break, self).save(*args, **kwargs)


# TODO: Actually implement booking reminder notifications
# class Notification(models.Model, TimeStampedModelMixin):
#     reservation = models.ForeignKey(
#         Reservation,
#         related_name="notifications",
#         on_delete=models.CASCADE,
#         null=True,
#         blank=True,
#     )
#     client = models.ForeignKey(
#         User,
#         verbose_name="Client",
#         related_name="notifications",
#         on_delete=models.CASCADE,
#         null=True,
#         blank=True,
#     )
#     time = models.DateTimeField(null=True, blank=True)
