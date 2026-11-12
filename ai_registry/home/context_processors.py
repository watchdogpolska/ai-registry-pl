from django.conf import settings


def app_version(request):
    source_url = settings.SOURCE_CODE_URL
    if settings.APP_COMMIT:
        source_url = f"{source_url}/tree/{settings.APP_COMMIT}"
    return {
        "APP_VERSION": settings.APP_VERSION,
        "APP_SOURCE_URL": source_url,
    }
