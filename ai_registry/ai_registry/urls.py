from django.conf import settings
from django.contrib import admin
from django.shortcuts import redirect
from django.templatetags.static import static
from django.urls import include, path


def favicon(request):
    return redirect(static("home/favicons/favicon.ico"))


urlpatterns = [
    path("favicon.ico", favicon),
    path("", include("home.urls")),
    path("admin/", admin.site.urls),
]

if settings.DEBUG and "debug_toolbar" in settings.INSTALLED_APPS:
    from debug_toolbar.toolbar import debug_toolbar_urls

    urlpatterns += debug_toolbar_urls()
