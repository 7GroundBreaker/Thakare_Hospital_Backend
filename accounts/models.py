from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.TextChoices):
    """Admin roles for the hospital CMS (see spec section 53 — Admin Roles).

    Fine-grained per-object permissions are implemented with Django's
    built-in Group/Permission system (configured in accounts/admin.py and
    the data migration that seeds default groups), rather than hand-rolled
    checks, so they stay editable from the Django admin without code changes.
    """

    SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"
    HOSPITAL_ADMIN = "HOSPITAL_ADMIN", "Hospital Admin"
    DOCTOR = "DOCTOR", "Doctor"
    RECEPTIONIST = "RECEPTIONIST", "Receptionist"
    CONTENT_EDITOR = "CONTENT_EDITOR", "Content Editor"
    MARKETING_ADMIN = "MARKETING_ADMIN", "Marketing Admin"


class User(AbstractUser):
    """Custom admin/staff user. Patients are never represented here —
    see appointments.Patient for public-facing appointment submissions."""

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.HOSPITAL_ADMIN)
    phone = models.CharField(max_length=20, blank=True)
    doctor_profile = models.OneToOneField(
        "hospital.Doctor",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="user_account",
        help_text="Link this account to a Doctor record when role = Doctor.",
    )

    def __str__(self):
        return self.get_full_name() or self.username
