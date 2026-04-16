from pathlib import Path
import os
from datetime import timezone as dt_timezone
from decouple import config

import django.utils.timezone as django_timezone

# Django 5.0+ removed django.utils.timezone.utc; some migrations/code still expect it.
if not hasattr(django_timezone, "utc"):
    django_timezone.utc = dt_timezone.utc

BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "django-insecure-change-me-for-production",
)

DEBUG = True

ALLOWED_HOSTS: list[str] = ["127.0.0.1", "localhost", "192.168.1.80", "72.61.78.9"]


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rentals",
    "users"
]


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF = "beach_rental_site.urls"


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
            ],
        },
    },
]


WSGI_APPLICATION = "beach_rental_site.wsgi.application"
ASGI_APPLICATION = "beach_rental_site.asgi.application"


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
 #       "ENGINE": "mysql.connector.django",
        "NAME": "u428340312_planetdestin",
        "USER": config('DB_USER'),
        "PASSWORD": config('DB_PASSWORD'),
        "HOST": "db.nikain.com",
        "PORT": "3306",
        "OPTIONS": {
            "charset": "utf8mb4", 
        },
    },
    "sqlite": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    },
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


LANGUAGE_CODE = "en-us"

TIME_ZONE = "America/New_York"

USE_I18N = True

USE_TZ = True


STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS: list[Path] = []


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "home"
AUTH_USER_MODEL = "users.CustomUser"
AUTHENTICATION_BACKENDS = [
    #"django.contrib.auth.backends.ModelBackend",
    "users.backends.PhoneOrEmailBackend",
]


RENTER_ENTRY_CODE = os.getenv("RENTER_ENTRY_CODE", "0000")
POOL_ACCESS_CODE = os.getenv("POOL_ACCESS_CODE", "1111")
WIFI_NETWORK_NAME = os.getenv("WIFI_NETWORK_NAME", "BeachHouseWifi")
WIFI_PASSWORD = os.getenv("WIFI_PASSWORD", "changeme123")
HOUSE_MANUAL_TEXT = os.getenv(
    "HOUSE_MANUAL_TEXT",
    "Welcome to your beachfront escape! Check-in is after 3pm, check-out is 10am. "
    "Please rinse off sand before using indoor showers and keep balcony doors closed "
    "when the A/C is running.",
)

