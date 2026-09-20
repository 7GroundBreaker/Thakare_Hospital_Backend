from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.text import slugify


class SEOFields(models.Model):
    """Reusable SEO fields (section 35/66 — SEO + structured data)."""

    seo_title = models.CharField(max_length=70, blank=True)
    seo_description = models.CharField(max_length=160, blank=True)
    canonical_url = models.URLField(blank=True)
    og_image = models.ImageField(upload_to="seo/og/", blank=True, null=True)

    class Meta:
        abstract = True


class TimeStamped(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class DayOfWeek(models.IntegerChoices):
    MONDAY = 0, "Monday"
    TUESDAY = 1, "Tuesday"
    WEDNESDAY = 2, "Wednesday"
    THURSDAY = 3, "Thursday"
    FRIDAY = 4, "Friday"
    SATURDAY = 5, "Saturday"
    SUNDAY = 6, "Sunday"


class Speciality(SEOFields, TimeStamped):
    """A medical speciality, e.g. Pediatrics (section 12 — Speciality pages)."""

    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    short_description = models.CharField(
        max_length=300,
        blank=True,
        help_text="Used on speciality cards (homepage + listing).",
    )
    description = models.TextField(
        blank=True, help_text="Full speciality description shown on the speciality page."
    )
    when_to_consult = models.TextField(
        blank=True, help_text="Guidance on when a patient should consult this speciality."
    )
    icon = models.CharField(
        max_length=60, blank=True, help_text="Icon identifier used by the frontend icon set."
    )
    hero_image = models.ImageField(upload_to="specialities/hero/", blank=True, null=True)
    card_image = models.ImageField(upload_to="specialities/card/", blank=True, null=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Specialities"
        ordering = ["display_order", "name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ConditionTreated(models.Model):
    """A condition/topic listed under a speciality page. CMS-managed content
    only — this list does NOT imply a specific treatment/procedure is
    offered unless separately confirmed by the hospital administrator."""

    speciality = models.ForeignKey(
        Speciality, on_delete=models.CASCADE, related_name="conditions_treated"
    )
    name = models.CharField(max_length=150)
    description = models.CharField(max_length=300, blank=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "name"]

    def __str__(self):
        return f"{self.name} ({self.speciality.name})"


class Service(SEOFields, TimeStamped):
    """A service/content-category offered under a speciality (section 9/12)."""

    speciality = models.ForeignKey(Speciality, on_delete=models.CASCADE, related_name="services")
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=170, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=60, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["display_order", "name"]
        unique_together = ("speciality", "slug")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Doctor(SEOFields, TimeStamped):
    """A doctor profile. Qualifications/experience/fees are left blank
    (CMS placeholders) until confirmed by the hospital administrator —
    see section 1 and section 58/59 for the "do not invent" rule."""

    full_name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=170, unique=True, blank=True)
    profile_photo = models.ImageField(upload_to="doctors/", blank=True, null=True)
    designation = models.CharField(max_length=150, blank=True)
    qualification = models.CharField(
        max_length=255, blank=True, help_text="TODO: leave blank until confirmed by the hospital."
    )
    specialities = models.ManyToManyField(Speciality, related_name="doctors")
    sub_speciality = models.CharField(max_length=150, blank=True)
    biography = models.TextField(blank=True)
    experience = models.CharField(
        max_length=100,
        blank=True,
        help_text="TODO: e.g. '10+ years' — leave blank until confirmed by the hospital.",
    )
    areas_of_expertise = models.TextField(
        blank=True, help_text="One item per line."
    )
    languages = models.CharField(max_length=200, blank=True, help_text="Comma-separated.")
    consultation_fee = models.CharField(
        max_length=50, blank=True, help_text="TODO: leave blank until confirmed by the hospital."
    )
    consultation_timings_note = models.CharField(
        max_length=200,
        blank=True,
        help_text="Optional free-text override; structured hours live in DoctorSchedule.",
    )
    clinic_location = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    whatsapp = models.CharField(max_length=20, blank=True)
    booking_enabled = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["display_order", "full_name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.full_name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.full_name

    @property
    def expertise_list(self):
        return [line.strip() for line in self.areas_of_expertise.splitlines() if line.strip()]

    @property
    def language_list(self):
        return [item.strip() for item in self.languages.split(",") if item.strip()]


class DoctorSchedule(models.Model):
    """Recurring weekly availability for a doctor (section 19)."""

    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="schedules")
    day_of_week = models.IntegerField(choices=DayOfWeek.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    break_start = models.TimeField(null=True, blank=True)
    break_end = models.TimeField(null=True, blank=True)
    slot_duration_minutes = models.PositiveIntegerField(default=30)
    max_appointments = models.PositiveIntegerField(
        default=0, help_text="0 = unlimited (derived from slot duration)."
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["day_of_week", "start_time"]
        unique_together = ("doctor", "day_of_week", "start_time")

    def __str__(self):
        return f"{self.doctor.full_name} — {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"


class DoctorLeave(models.Model):
    """A date (or date range day) a doctor is unavailable (section 19)."""

    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="leaves")
    date = models.DateField()
    reason = models.CharField(max_length=255, blank=True)
    full_day = models.BooleanField(default=True)

    class Meta:
        ordering = ["date"]
        unique_together = ("doctor", "date")

    def __str__(self):
        return f"{self.doctor.full_name} unavailable on {self.date}"


class SiteSettings(models.Model):
    """Singleton hospital-wide settings (section 34). Use SiteSettings.load()
    to fetch the single configured row; TODO placeholders are used for any
    hospital-provided detail (address, phone, coordinates, etc.) that has
    not yet been supplied."""

    hospital_name = models.CharField(max_length=150, default="Thakare Hospital")
    logo = models.ImageField(upload_to="branding/", blank=True, null=True)
    favicon = models.ImageField(upload_to="branding/", blank=True, null=True)
    hero_image = models.ImageField(
        upload_to="branding/", blank=True, null=True, help_text="Homepage hero photograph."
    )
    about_image = models.ImageField(
        upload_to="branding/",
        blank=True,
        null=True,
        help_text="Hospital building/exterior photograph used on the About sections.",
    )
    tagline = models.CharField(max_length=200, blank=True)

    phone = models.CharField(max_length=20, blank=True, help_text="TODO: [HOSPITAL PHONE]")
    whatsapp_number = models.CharField(max_length=20, blank=True, help_text="TODO: [WHATSAPP NUMBER]")
    whatsapp_message_template = models.CharField(
        max_length=300,
        blank=True,
        default="Hello Thakare Hospital, I would like to book an appointment.",
    )
    email = models.EmailField(blank=True, help_text="TODO: [HOSPITAL EMAIL]")
    address = models.TextField(blank=True, help_text="TODO: [HOSPITAL ADDRESS]")

    google_maps_url = models.URLField(blank=True, help_text="TODO: [GOOGLE MAPS URL]")
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)

    opening_hours = models.TextField(
        blank=True, help_text="TODO: e.g. 'Mon-Sat: 9:00 AM - 8:00 PM'"
    )

    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    google_review_url = models.URLField(blank=True)

    emergency_enabled = models.BooleanField(default=False)
    emergency_phone = models.CharField(max_length=20, blank=True)
    emergency_availability = models.CharField(max_length=100, blank=True)
    emergency_message = models.CharField(max_length=255, blank=True)

    privacy_policy = models.TextField(blank=True)
    terms_and_conditions = models.TextField(blank=True)
    medical_disclaimer = models.TextField(
        blank=True,
        default=(
            "Information provided on this website is for general educational "
            "purposes and should not be considered a substitute for professional "
            "medical advice."
        ),
    )
    footer_description = models.TextField(blank=True)

    google_analytics_id = models.CharField(max_length=40, blank=True)
    google_tag_manager_id = models.CharField(max_length=40, blank=True)

    ai_assistant_enabled = models.BooleanField(
        default=False,
        help_text="Master switch for the future AI assistant (section 51/52). Off by default.",
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return self.hospital_name

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
