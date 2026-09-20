"""URL configuration for the Thakare Hospital backend.

Public read/write API lives under /api/v1/. The Django admin (session
authenticated, staff-only) at /admin/ is the hospital CMS and appointment
dashboard — no equivalent admin CRUD is exposed through the DRF API.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from hospital.views import SiteSettingsView

api_v1_patterns = [
    path("", include("hospital.urls")),
    path("", include("appointments.urls")),
    path("", include("content.urls")),
    path("settings/", SiteSettingsView.as_view(), name="site-settings"),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include(api_v1_patterns)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
