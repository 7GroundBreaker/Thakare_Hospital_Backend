from rest_framework import permissions
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from accounts.models import Role
from hospital.models import Doctor

from . import services

ADMIN_ROLES = {Role.SUPER_ADMIN, Role.HOSPITAL_ADMIN, Role.RECEPTIONIST}


class QueueDisplayThrottle(AnonRateThrottle):
    scope = "queue_display"


def is_queue_admin(user):
    return user.is_superuser or user.role in ADMIN_ROLES


def can_manage_queue(user):
    if not (user and user.is_authenticated and user.is_active and user.is_staff):
        return False
    if is_queue_admin(user):
        return True
    return user.role == Role.DOCTOR and user.doctor_profile_id is not None


def resolve_doctor_id(user, requested):
    """Doctors operate only on their own queue; admin/reception staff must
    name a doctor. Returns None when the caller may not act on it."""
    try:
        requested = int(requested) if requested else None
    except (TypeError, ValueError):
        return None
    if is_queue_admin(user):
        return requested
    if requested and requested != user.doctor_profile_id:
        return None
    return user.doctor_profile_id


class CanManageQueue(permissions.BasePermission):
    message = "You are not allowed to manage the token queue."

    def has_permission(self, request, view):
        return can_manage_queue(request.user)


class QueueAPIView(APIView):
    """Used by the token panel inside the Django admin, so it authenticates
    with the admin session (CSRF enforced by SessionAuthentication)."""

    authentication_classes = [SessionAuthentication]
    permission_classes = [CanManageQueue]

    def doctor(self, request):
        requested = request.data.get("doctor") or request.query_params.get("doctor")
        doctor_id = resolve_doctor_id(request.user, requested)
        if doctor_id is None:
            self.permission_denied(request, message="Choose a doctor you are allowed to manage.")
        try:
            return Doctor.objects.get(pk=doctor_id)
        except Doctor.DoesNotExist:
            raise services.QueueError("Doctor not found.", 404)

    def handle_exception(self, exc):
        if isinstance(exc, services.QueueError):
            return Response({"detail": exc.message}, status=exc.status_code)
        return super().handle_exception(exc)

    def state(self, doctor):
        return Response(services.doctor_state(doctor))


class QueueView(QueueAPIView):
    def get(self, request):
        return self.state(self.doctor(request))


class CallNumberView(QueueAPIView):
    def post(self, request, number):
        doctor = self.doctor(request)
        services.call_number(doctor.id, number)
        return self.state(doctor)


class UnexaminedView(QueueAPIView):
    def post(self, request, number):
        doctor = self.doctor(request)
        services.mark_unexamined(doctor.id, number)
        return self.state(doctor)


class CallNextView(QueueAPIView):
    def post(self, request):
        doctor = self.doctor(request)
        services.call_next(doctor.id)
        return self.state(doctor)


class CompleteView(QueueAPIView):
    def post(self, request):
        doctor = self.doctor(request)
        services.complete_current(doctor.id)
        return self.state(doctor)


class PublicDisplayView(APIView):
    """Waiting-room monitor data. Public and deliberately minimal: token
    numbers plus doctor name/room, never any patient information."""

    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    throttle_classes = [QueueDisplayThrottle]

    def get(self, request):
        return Response(services.display_state())
