from .base import *

DEBUG = False
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="ci-test-secret-key-not-for-production-use",
)
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]
