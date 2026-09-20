from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from .models import Appointment
from .serializers import AppointmentCreateSerializer, AppointmentStatusSerializer


class AppointmentSubmitThrottle(AnonRateThrottle):
    scope = "appointment_submit"


class AppointmentCreateView(generics.CreateAPIView):
    """Public appointment booking endpoint (section 16/17).

    Intentionally does not expose list/update/delete — admin management of
    appointments happens exclusively through the authenticated Django admin
    (section 41 — admin APIs must never be public).
    """

    queryset = Appointment.objects.all()
    serializer_class = AppointmentCreateSerializer
    throttle_classes = [AppointmentSubmitThrottle]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        appointment = serializer.save()
        return Response(
            AppointmentStatusSerializer(appointment).data,
            status=status.HTTP_201_CREATED,
        )


class AppointmentStatusView(generics.RetrieveAPIView):
    """Look up an appointment's status by its reference ID only — no listing,
    no patient-identifying search, to avoid leaking other patients' data."""

    queryset = Appointment.objects.all()
    serializer_class = AppointmentStatusSerializer
    lookup_field = "reference_id"
    lookup_url_kwarg = "reference_id"
