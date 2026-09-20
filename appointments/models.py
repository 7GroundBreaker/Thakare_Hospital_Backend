import random
import string

from django.core.validators import FileExtensionValidator
from django.db import models

from hospital.models import Doctor, Speciality


def generate_reference_id():
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"TH-{suffix}"


class Gender(models.TextChoices):
    MALE = "MALE", "Male"
    FEMALE = "FEMALE", "Female"
    OTHER = "OTHER", "Other"
    PREFER_NOT_TO_SAY = "PREFER_NOT_TO_SAY", "Prefer not to say"


class Patient(models.Model):
    """A patient as captured from an appointment request. Deliberately
    minimal — this is not a full EMR/patient record system."""

    full_name = models.CharField(max_length=150)
    mobile_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=Gender.choices, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.full_name} ({self.mobile_number})"


class AppointmentType(models.TextChoices):
    IN_PERSON = "IN_PERSON", "In-person consultation"
    ONLINE = "ONLINE", "Online consultation"
    FOLLOW_UP = "FOLLOW_UP", "Follow-up visit"


class AppointmentStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    CONFIRMED = "CONFIRMED", "Confirmed"
    RESCHEDULED = "RESCHEDULED", "Rescheduled"
    COMPLETED = "COMPLETED", "Completed"
    CANCELLED = "CANCELLED", "Cancelled"
    NO_SHOW = "NO_SHOW", "No-show"


def report_upload_path(instance, filename):
    return f"appointment-reports/{instance.reference_id}/{filename}"


class Appointment(models.Model):
    """An appointment request submitted from the public website
    (section 16/17 — Appointment System & Workflow)."""

    reference_id = models.CharField(max_length=20, unique=True, editable=False, blank=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="appointments")
    speciality = models.ForeignKey(
        Speciality, on_delete=models.SET_NULL, null=True, related_name="appointments"
    )
    doctor = models.ForeignKey(
        Doctor, on_delete=models.SET_NULL, null=True, blank=True, related_name="appointments"
    )
    preferred_date = models.DateField()
    preferred_time = models.TimeField()
    appointment_type = models.CharField(
        max_length=20, choices=AppointmentType.choices, default=AppointmentType.IN_PERSON
    )
    reason_for_visit = models.TextField(blank=True)
    additional_message = models.TextField(blank=True)
    report_upload = models.FileField(
        upload_to=report_upload_path,
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=["pdf", "jpg", "jpeg", "png"])],
        help_text="Stored privately — never exposed via a public URL.",
    )
    consent_given = models.BooleanField(default=False)

    status = models.CharField(
        max_length=20, choices=AppointmentStatus.choices, default=AppointmentStatus.PENDING
    )
    admin_notes = models.TextField(blank=True, help_text="Internal notes, not visible to patients.")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "preferred_date"]),
            models.Index(fields=["doctor", "preferred_date"]),
        ]

    def save(self, *args, **kwargs):
        if not self.reference_id:
            reference_id = generate_reference_id()
            while Appointment.objects.filter(reference_id=reference_id).exists():
                reference_id = generate_reference_id()
            self.reference_id = reference_id
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.reference_id} — {self.patient.full_name}"
