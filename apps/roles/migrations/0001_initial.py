# Generated by Django 5.1 on 2024-08-28 14:53

import datetime

import django.contrib.auth.models
import django.contrib.auth.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models

import djmoney.models.fields
import timezone_field.fields
import utils.db


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                ("last_login", models.DateTimeField(blank=True, null=True, verbose_name="last login")),
                (
                    "is_superuser",
                    models.BooleanField(
                        default=False,
                        help_text="Designates that this user has all permissions without explicitly assigning them.",
                        verbose_name="superuser status",
                    ),
                ),
                (
                    "username",
                    models.CharField(
                        error_messages={"unique": "A user with that username already exists."},
                        help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.",
                        max_length=150,
                        unique=True,
                        validators=[django.contrib.auth.validators.UnicodeUsernameValidator()],
                        verbose_name="username",
                    ),
                ),
                ("first_name", models.CharField(blank=True, max_length=150, verbose_name="first name")),
                ("email", models.EmailField(blank=True, max_length=254, verbose_name="email address")),
                (
                    "is_staff",
                    models.BooleanField(
                        default=False,
                        help_text="Designates whether the user can log into this admin site.",
                        verbose_name="staff status",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="Designates whether this user should be treated as active. Unselect this instead of deleting accounts.",
                        verbose_name="active",
                    ),
                ),
                ("date_joined", models.DateTimeField(default=django.utils.timezone.now, verbose_name="date joined")),
                ("tg_id", models.BigIntegerField(blank=True, null=True, unique=True, verbose_name="Telegram user ID")),
                (
                    "tg_username",
                    models.CharField(
                        blank=True, max_length=50, null=True, unique=True, verbose_name="Telegram username"
                    ),
                ),
                ("last_name", models.CharField(blank=True, max_length=150, null=True, verbose_name="Last name")),
                (
                    "phone",
                    models.CharField(blank=True, max_length=25, null=True, unique=True, verbose_name="Phone number"),
                ),
                ("locale", models.CharField(blank=True, max_length=10, null=True, verbose_name="Locale")),
                ("full_name", models.CharField(blank=True, max_length=100, null=True, verbose_name="Full name")),
                ("provider_created", models.BooleanField(default=False, verbose_name="Provider created")),
                (
                    "tz",
                    timezone_field.fields.TimeZoneField(default="Europe/Kyiv", use_pytz=False, verbose_name="Timezone"),
                ),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={
                "verbose_name": "user",
                "verbose_name_plural": "users",
                "abstract": False,
            },
            bases=(models.Model, utils.db.TimeStampedModelMixin),
            managers=[
                ("objects", django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name="Provider",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("phone", models.CharField(blank=True, max_length=25, null=True, verbose_name="Work phone number")),
                ("email", models.EmailField(blank=True, max_length=254, null=True, verbose_name="Work email")),
                ("start", utils.db.NormalizedTimeField(default=datetime.time(9, 0))),
                ("end", models.TimeField(default=datetime.time(18, 0))),
                ("lunch_start", utils.db.NormalizedTimeField(blank=True, null=True)),
                ("lunch_end", utils.db.NormalizedTimeField(blank=True, null=True)),
                ("weekend", models.CharField(blank=True, default="56", max_length=7, verbose_name="Weekly days off")),
                ("slot", utils.db.NormalizedDurationField(default=15)),
                ("currency", djmoney.models.fields.CurrencyField(default="UAH", max_length=3)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="provider",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            bases=(models.Model, utils.db.TimeStampedModelMixin),
        ),
    ]
