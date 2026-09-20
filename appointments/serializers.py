from django.conf import settings
from django.utils import timezone
from rest_framework import serializers

from hospital.models import Doctor, Speciality

from .models import Appointment, Patient


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ("full_name", "mobile_number", "email", "date_of_birth", "gender")


class AppointmentCreateSerializer(serializers.ModelSerializer):
    """Public appointment-request submission (section 16/17).

    Patient details are nested and created together with the appointment.
    """

    full_name = serializers.CharField(write_only=True, max_length=150)
    mobile_number = serializers.CharField(write_only=True, max_length=20)
    email = serializers.EmailField(write_only=True, required=False, allow_blank=True)
    date_of_birth = serializers.DateField(write_only=True, required=False, allow_null=True)
    gender = serializers.ChoiceField(
        choices=Patient._meta.get_field("gender").choices, write_only=True, required=False, allow_blank=True
    )
    speciality = serializers.SlugRelatedField(slug_field="slug", queryset=Speciality.objects.filter(is_active=True))
    doctor = serializers.SlugRelatedField(
        slug_field="slug", queryset=Doctor.objects.filter(is_active=True), required=False, allow_null=True
    )
    consent_given = serializers.BooleanField()

    class Meta:
        model = Appointment
        fields = (
            "full_name",
            "mobile_number",
            "email",
            "date_of_birth",
            "gender",
            "speciality",
            "doctor",
            "preferred_date",
            "preferred_time",
            "appointment_type",
            "reason_for_visit",
            "additional_message",
            "report_upload",
            "consent_given",
            "reference_id",
            "status",
        )
        read_only_fields = ("reference_id", "status")

    def validate_consent_given(self, value):
        if not value:
            raise serializers.ValidationError(
                "You must agree to be contacted regarding your appointment request."
            )
        return value

    def validate_preferred_date(self, value):
        if value < timezone.localdate():
            raise serializers.ValidationError("Preferred date cannot be in the past.")
        return value

    def validate_report_upload(self, file_obj):
        if not file_obj:
            return file_obj
        max_bytes = settings.APPOINTMENT_MAX_UPLOAD_MB * 1024 * 1024
        if file_obj.size > max_bytes:
            raise serializers.ValidationError(
                f"File is too large. Maximum allowed size is {settings.APPOINTMENT_MAX_UPLOAD_MB}MB."
            )
        extension = file_obj.name.rsplit(".", 1)[-1].lower() if "." in file_obj.name else ""
        if extension not in settings.APPOINTMENT_ALLOWED_UPLOAD_EXTENSIONS:
            allowed = ", ".join(settings.APPOINTMENT_ALLOWED_UPLOAD_EXTENSIONS)
            raise serializers.ValidationError(f"Unsupported file type. Allowed formats: {allowed}.")
        return file_obj

    def create(self, validated_data):
        patient_data = {
            "full_name": validated_data.pop("full_name"),
            "mobile_number": validated_data.pop("mobile_number"),
            "email": validated_data.pop("email", ""),
            "date_of_birth": validated_data.pop("date_of_birth", None),
            "gender": validated_data.pop("gender", ""),
        }
        patient = Patient.objects.create(**patient_data)
        appointment = Appointment.objects.create(patient=patient, **validated_data)
        return appointment


class AppointmentStatusSerializer(serializers.ModelSerializer):
    """Minimal public status-lookup response (used by the confirmation page)."""

    doctor = serializers.CharField(source="doctor.full_name", default="", read_only=True)
    speciality = serializers.CharField(source="speciality.name", default="", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Appointment
        fields = (
            "reference_id",
            "status",
            "status_display",
            "doctor",
            "speciality",
            "preferred_date",
            "preferred_time",
            "created_at",
        )
