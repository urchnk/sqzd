# Generated by Django 5.1 on 2024-08-28 13:56

from django.db import migrations

import djmoney.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ("scheduler", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="reservation",
            name="price_currency",
            field=djmoney.models.fields.CurrencyField(
                choices=[
                    ("GBP", "British Pound"),
                    ("CAD", "Canadian Dollar"),
                    ("CZK", "Czech Koruna"),
                    ("DKK", "Danish Krone"),
                    ("EUR", "Euro"),
                    ("MDL", "Moldovan Leu"),
                    ("NOK", "Norwegian Krone"),
                    ("PLN", "Polish Zloty"),
                    ("RON", "Romanian Leu"),
                    ("SEK", "Swedish Krona"),
                    ("CHF", "Swiss Franc"),
                    ("USD", "US Dollar"),
                    ("UAH", "Ukrainian Hryvnia"),
                ],
                default="UAH",
                editable=False,
                max_length=3,
                null=True,
            ),
        ),
    ]
