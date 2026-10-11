from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.urls import reverse

from accounts.models import Role
from hospital.models import Doctor

from .models import QueueToken
from .views import can_manage_queue, is_queue_admin


@admin.register(QueueToken)
class QueueTokenAdmin(admin.ModelAdmin):
    list_display = ("doctor", "service_date", "number", "status", "called_at", "completed_at")
    list_filter = ("service_date", "status", "doctor")
    date_hierarchy = "service_date"

    # History is written only by the token panel; keep it read-only here.
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


def token_panel(request):
    """Mobile-first page inside the admin where a doctor taps the token
    number they are seeing. Wrapped with admin_view() in config/urls.py."""
    if not can_manage_queue(request.user):
        raise PermissionDenied
    staff = is_queue_admin(request.user)
    return render(
        request,
        "admin/queueing/token_panel.html",
        {
            **admin.site.each_context(request),
            "title": "Token Panel",
            "own_doctor": request.user.doctor_profile,
            "doctors": Doctor.objects.filter(is_active=True) if staff else [],
        },
    )


def admin_index(request, extra_context=None):
    """Send doctors straight to their token panel after logging in to the
    admin; everyone else gets the normal admin index."""
    user = request.user
    if user.role == Role.DOCTOR and not is_queue_admin(user) and can_manage_queue(user):
        return redirect(reverse("token-panel"))
    return admin.site.index(request, extra_context)
