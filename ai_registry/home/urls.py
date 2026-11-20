from django.urls import path

from .views import AIUseDetailView, HomeView, RobotsTxtView, XLSXExportView

urlpatterns = [
    path("", HomeView.as_view(), name="home_view"),
    path(
        "zastosowania/<uuid:public_id>/",
        AIUseDetailView.as_view(),
        name="ai_use_detail",
    ),
    path("robots.txt", RobotsTxtView.as_view(), name="robots_txt"),
    path("export/data.xlsx", XLSXExportView.as_view(), name="xlsx_export"),
]
