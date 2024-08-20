from django.db import models

from apps.roles.models import Provider
from djmoney.models.fields import MoneyField
from utils.db import NormalizedDurationField, TimeStampedModelMixin


class Service(models.Model, TimeStampedModelMixin):
    name = models.CharField(verbose_name="Service name", max_length=50)
    providers = models.ManyToManyField(
        Provider,
        verbose_name="Providers",
        related_name="services",
    )
    price = MoneyField(max_digits=14, decimal_places=2, null=True, default_currency="UAH")
    description = models.TextField(verbose_name="Description", max_length=255, blank=True, null=True)
    duration = NormalizedDurationField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"№{self.id} - {self.name}"
