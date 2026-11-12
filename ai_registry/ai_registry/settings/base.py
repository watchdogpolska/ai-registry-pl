import os
from pathlib import Path

import environ
from django.utils.log import DEFAULT_LOGGING

BASE_DIR = Path(__file__).resolve().parent.parent.parent
env = environ.Env()

# Log to console even when DEBUG is off.
DEFAULT_LOGGING["handlers"]["console"]["filters"] = []

INSTALLED_APPS = [
    "home.apps.HomeConfig",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "taggit",
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

ROOT_URLCONF = "ai_registry.urls"

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

WSGI_APPLICATION = "ai_registry.wsgi.application"

DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default="mysql://django:changeme@mysql:3306/django",
    )
}
DATABASES["default"].setdefault("OPTIONS", {})
DATABASES["default"]["OPTIONS"].update(
    {
        "charset": "utf8mb4",
        "init_command": "SET NAMES 'utf8mb4' COLLATE 'utf8mb4_polish_ci'",
    }
)

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

LANGUAGE_CODE = "pl"
LANGUAGES = [("pl", "Polish")]
TIME_ZONE = "Europe/Warsaw"
USE_I18N = True
USE_TZ = True

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

STATIC_ROOT = BASE_DIR / "staticfiles"
STATIC_URL = "/static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Tag values entered in the admin are separated with semicolons.
TAGGIT_TAGS_FROM_STRING = "home.models.tags.custom_tag_string_parser"
TAGGIT_STRING_FROM_TAGS = "home.models.tags.custom_tag_string_joiner"

# Keep admin edits immediately visible unless caching is explicitly enabled.
HOME_PAGE_CACHE_SECONDS = env.int("DJANGO_HOME_PAGE_CACHE_SECONDS", default=0)
