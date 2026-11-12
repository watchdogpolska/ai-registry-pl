from django.core.exceptions import ImproperlyConfigured

from .base import *


def required_list(name):
    value = env(name, default="").strip()
    if not value:
        raise ImproperlyConfigured(f"{name} must be set in production.")
    return [item.strip() for item in value.split(",") if item.strip()]


DEBUG = False

SECRET_KEY = env("DJANGO_SECRET_KEY")
ALLOWED_HOSTS = required_list("DJANGO_ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = required_list("DJANGO_CSRF_TRUSTED_ORIGINS")

DATABASES = {"default": env.db("DATABASE_URL")}
DATABASES["default"].setdefault("OPTIONS", {})
DATABASES["default"]["OPTIONS"].update(
    {
        "charset": "utf8mb4",
        "init_command": "SET NAMES 'utf8mb4' COLLATE 'utf8mb4_polish_ci'",
    }
)

MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
STORAGES["staticfiles"] = {
    "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
}

# Enable only when the reverse proxy overwrites X-Forwarded-Proto.
if env.bool("DJANGO_TRUST_X_FORWARDED_PROTO", default=False):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=False)
SESSION_COOKIE_SECURE = env.bool("DJANGO_SESSION_COOKIE_SECURE", default=True)
CSRF_COOKIE_SECURE = env.bool("DJANGO_CSRF_COOKIE_SECURE", default=True)
