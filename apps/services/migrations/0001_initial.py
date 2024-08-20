# Generated by Django 5.1 on 2024-08-20 19:31

from django.db import migrations, models

import djmoney.models.fields
import utils.db


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("roles", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Service",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=50, verbose_name="Service name")),
                (
                    "price_currency",
                    djmoney.models.fields.CurrencyField(
                        choices=[("EUR", "EUR €"), ("UAH", "UAH ₴"), ("USD", "USD $")],
                        default="UAH",
                        editable=False,
                        max_length=3,
                        null=True,
                    ),
                ),
                (
                    "price",
                    djmoney.models.fields.MoneyField(
                        decimal_places=2, default_currency="UAH", max_digits=14, null=True
                    ),
                ),
                ("description", models.TextField(blank=True, max_length=255, null=True, verbose_name="Description")),
                ("duration", utils.db.NormalizedDurationField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "providers",
                    models.ManyToManyField(related_name="services", to="roles.provider", verbose_name="Providers"),
                ),
            ],
            bases=(models.Model, utils.db.TimeStampedModelMixin),
        ),
    ]
