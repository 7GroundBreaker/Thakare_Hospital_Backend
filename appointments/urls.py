from django.urls import path

from .views import AppointmentCreateView, AppointmentStatusView

urlpatterns = [
    path("appointments/", AppointmentCreateView.as_view(), name="appointment-create"),
    path(
        "appointments/<str:reference_id>/status/",
        AppointmentStatusView.as_view(),
        name="appointment-status",
    ),
]
