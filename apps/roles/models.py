from datetime import time

from django.contrib.auth.models import AbstractUser
from django.db import models

from utils.db import NormalizedDurationField, NormalizedTimeField, TimeStampedModelMixin


class User(AbstractUser, TimeStampedModelMixin):
    tg_id = models.BigIntegerField(verbose_name="Telegram user ID", unique=True, blank=True, null=True)
    tg_username = models.CharField(
        verbose_name="Telegram username",
        max_length=50,
        unique=True,
        blank=True,
        null=True,
    )
    last_name = models.CharField(verbose_name="Last name", max_length=150, null=True, blank=True)
    phone = models.CharField(verbose_name="Phone number", max_length=25, null=True, blank=True)
    locale = models.CharField(verbose_name="Locale", max_length=10, blank=True, null=True)
    full_name = models.CharField(verbose_name="Full name", max_length=100, blank=True, null=True)
    provider_created = models.BooleanField(verbose_name="Provider created", default=False)

    def save(self, *args, **kwargs):
        if not self.last_name:
            self.last_name = ""
        self.full_name = self.get_full_name()
        super().save(*args, **kwargs)

    def is_provider(self) -> bool:
        return Provider.objects.filter(user=self).exists()

    def __str__(self):
        return f"{self.pk} - {self.full_name}"


class Provider(models.Model, TimeStampedModelMixin):
    user = models.OneToOneField(User, related_name="provider", on_delete=models.CASCADE)
    phone = models.CharField(verbose_name="Work phone number", max_length=25, null=True, blank=True)
    email = models.EmailField(verbose_name="Work email", blank=True, null=True)
    start = NormalizedTimeField(default=time(hour=9))
    end = models.TimeField(default=time(hour=18))
    lunch_start = NormalizedTimeField(null=True, blank=True)
    lunch_end = NormalizedTimeField(null=True, blank=True)
    # String of numerical weekday values. Default: Saturday, Sunday (56).
    days_off = models.CharField(verbose_name="Weekly days off", max_length=7, default="56", blank=True)
    slot = NormalizedDurationField(default=15)

    def __str__(self):
        return f"{self.user}"


class Company(models.Model, TimeStampedModelMixin):
    name = models.CharField(verbose_name="Company name", max_length=50)

    class Meta:
        verbose_name_plural = "Companies"


class Office(models.Model, TimeStampedModelMixin):
    name = models.CharField(verbose_name="Office name", max_length=50)
