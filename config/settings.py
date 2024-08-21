"""
Django settings for django_project1 project.

Generated by 'django-admin startproject' using Django 3.2.12.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""

import sys
from pathlib import Path

from django.utils.translation import gettext_lazy as _

import environ
from dotenv import load_dotenv

load_dotenv()
env = environ.Env()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.str("DJANGO_SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("DEBUG", False)
TESTING = len(sys.argv) > 1 and sys.argv[1] == "test"

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", [])

# Application definition

INSTALLED_APPS = [
    "modeltranslation",  # Must be placed before django.contrib.admin
    # Django native
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "django_extensions",
    "djmoney",
    # Proprietary
    "apps.roles",
    "apps.scheduler",
    "apps.services",
    "apps.texts",
]

AUTH_USER_MODEL = "roles.User"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.locale.LocaleMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

WSGI_APPLICATION = "config.wsgi.application"


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

if TESTING:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": "testdb",
            "USER": "tester",
            "PASSWORD": "testpassword",
            "HOST": "localhost",
            "PORT": "5432",
            "TEST": {
                "NAME": "testdb",
            },
        }
    }
else:
    DATABASES = {"default": env.db("DATABASE_URL", default="")}

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = "uk"

LANGUAGES = (
    # Default language (needs to stay first):
    ("en", _("English")),
    # Other supported languages (ordered by most widely supported):
    ("uk", _("Ukrainian")),
)
LANGUAGES_CODES = {lang[0] for lang in LANGUAGES}
MODELTRANSLATION_DEFAULT_LANGUAGE = "en"

TIME_ZONE = "Europe/Kyiv"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = "/static/"

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CURRENCIES = ("USD", "EUR", "UAH")
CURRENCY_CHOICES = [("USD", "USD $"), ("EUR", "EUR €"), ("UAH", "UAH ₴")]

LOCALE_PATHS = [BASE_DIR / "locales"]

ALLOWED_TG_USERS = env.list("ALLOWED_TG_USERS", [])
