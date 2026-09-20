import csv

from django.contrib import admin
from django.http import HttpResponse

from .models import Appointment, Patient


class AppointmentReportPresentFilter(admin.SimpleListFilter):
    title = "report uploaded"
    parameter_name = "has_report"

    def lookups(self, request, model_admin):
        return (("yes", "Yes"), ("no", "No"))

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.exclude(report_upload="")
        if self.value() == "no":
            return queryset.filter(report_upload="")
        return queryset


@admin.action(description="Export selected appointments to CSV")
def export_appointments_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="appointments.csv"'
    writer = csv.writer(response)
    writer.writerow(
        [
            "Reference ID",
            "Patient",
            "Mobile",
            "Doctor",
            "Speciality",
            "Preferred date",
            "Preferred time",
            "Type",
            "Status",
            "Created at",
        ]
    )
    for appointment in queryset.select_related("patient", "doctor", "speciality"):
        writer.writerow(
            [
                appointment.reference_id,
                appointment.patient.full_name,
                appointment.patient.mobile_number,
                appointment.doctor.full_name if appointment.doctor else "",
                appointment.speciality.name if appointment.speciality else "",
                appointment.preferred_date,
                appointment.preferred_time,
                appointment.get_appointment_type_display(),
                appointment.get_status_display(),
                appointment.created_at,
            ]
        )
    return response


@admin.action(description="Mark selected as Confirmed")
def mark_confirmed(modeladmin, request, queryset):
    queryset.update(status="CONFIRMED")


@admin.action(description="Mark selected as Cancelled")
def mark_cancelled(modeladmin, request, queryset):
    queryset.update(status="CANCELLED")


@admin.action(description="Mark selected as Completed")
def mark_completed(modeladmin, request, queryset):
    queryset.update(status="COMPLETED")


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    date_hierarchy = "preferred_date"
    list_display = (
        "reference_id",
        "patient_name",
        "patient_mobile",
        "doctor",
        "speciality",
        "preferred_date",
        "preferred_time",
        "status",
        "created_at",
    )
    list_filter = ("status", "doctor", "speciality", "appointment_type", AppointmentReportPresentFilter)
    search_fields = ("reference_id", "patient__full_name", "patient__mobile_number", "patient__email")
    list_editable = ("status",)
    readonly_fields = ("reference_id", "created_at", "updated_at")
    autocomplete_fields = ("doctor", "speciality")
    actions = [export_appointments_csv, mark_confirmed, mark_cancelled, mark_completed]
    fieldsets = (
        ("Reference", {"fields": ("reference_id", "status", "admin_notes")}),
        ("Patient", {"fields": ("patient",)}),
        ("Appointment details", {"fields": ("speciality", "doctor", "appointment_type", "preferred_date", "preferred_time")}),
        ("Patient notes", {"fields": ("reason_for_visit", "additional_message", "report_upload", "consent_given")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    @admin.display(description="Patient", ordering="patient__full_name")
    def patient_name(self, obj):
        return obj.patient.full_name

    @admin.display(description="Mobile")
    def patient_mobile(self, obj):
        return obj.patient.mobile_number


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("full_name", "mobile_number", "email", "gender", "created_at")
    search_fields = ("full_name", "mobile_number", "email")
    list_filter = ("gender",)
