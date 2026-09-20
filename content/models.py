from django.db import models
from django.utils.text import slugify

from hospital.models import Doctor, SEOFields, Speciality


class ArticleCategory(models.Model):
    """Health Library category (section 23) — e.g. Pediatrics, Women's Health."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name_plural = "Article categories"
        ordering = ["display_order", "name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Article(SEOFields):
    """A Health Library article (section 23/24)."""

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    featured_image = models.ImageField(upload_to="articles/", blank=True, null=True)
    category = models.ForeignKey(
        ArticleCategory, on_delete=models.SET_NULL, null=True, related_name="articles"
    )
    speciality = models.ForeignKey(
        Speciality, on_delete=models.SET_NULL, null=True, blank=True, related_name="articles"
    )
    author = models.CharField(max_length=150, blank=True)
    publish_date = models.DateField(null=True, blank=True)
    short_description = models.CharField(max_length=300, blank=True)
    content = models.TextField(blank=True, help_text="Article body (HTML/rich text).")
    key_takeaways = models.TextField(blank=True, help_text="One point per line.")
    tags = models.CharField(max_length=300, blank=True, help_text="Comma-separated.")
    related_articles = models.ManyToManyField("self", blank=True, symmetrical=True)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-publish_date", "-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    @property
    def tag_list(self):
        return [t.strip() for t in self.tags.split(",") if t.strip()]

    @property
    def takeaway_list(self):
        return [t.strip() for t in self.key_takeaways.splitlines() if t.strip()]


class FAQCategory(models.TextChoices):
    APPOINTMENTS = "APPOINTMENTS", "Appointments"
    PEDIATRICS = "PEDIATRICS", "Pediatrics"
    WOMENS_HEALTH = "WOMENS_HEALTH", "Women's Health"
    DENTAL_CARE = "DENTAL_CARE", "Dental Care"
    HOSPITAL = "HOSPITAL", "Hospital"
    PAYMENTS = "PAYMENTS", "Payments"
    REPORTS = "REPORTS", "Reports"
    GENERAL = "GENERAL", "General"


class FAQ(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    category = models.CharField(max_length=30, choices=FAQCategory.choices, default=FAQCategory.GENERAL)
    speciality = models.ForeignKey(
        Speciality, on_delete=models.SET_NULL, null=True, blank=True, related_name="faqs"
    )
    display_order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)

    class Meta:
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"
        ordering = ["category", "display_order"]

    def __str__(self):
        return self.question


class Testimonial(models.Model):
    """Genuine patient feedback only — never fabricated (section 25)."""

    patient_name = models.CharField(max_length=150)
    testimonial_text = models.TextField()
    speciality = models.ForeignKey(
        Speciality, on_delete=models.SET_NULL, null=True, blank=True, related_name="testimonials"
    )
    doctor = models.ForeignKey(
        Doctor, on_delete=models.SET_NULL, null=True, blank=True, related_name="testimonials"
    )
    photo = models.ImageField(upload_to="testimonials/", blank=True, null=True)
    rating = models.PositiveSmallIntegerField(null=True, blank=True, help_text="1-5, optional.")
    date = models.DateField(null=True, blank=True)
    consent_confirmed = models.BooleanField(
        default=False,
        help_text="Confirm the patient consented to publishing this testimonial before publishing it.",
    )
    is_published = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "-date"]

    def __str__(self):
        return f"{self.patient_name} — {self.date or 'undated'}"


class GalleryCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name_plural = "Gallery categories"
        ordering = ["display_order", "name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class GalleryImage(models.Model):
    category = models.ForeignKey(GalleryCategory, on_delete=models.SET_NULL, null=True, related_name="images")
    image = models.ImageField(upload_to="gallery/")
    caption = models.CharField(max_length=200, blank=True)
    is_featured = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["display_order", "-created_at"]

    def __str__(self):
        return self.caption or f"Gallery image #{self.pk}"


class EnquiryStatus(models.TextChoices):
    NEW = "NEW", "New"
    CONTACTED = "CONTACTED", "Contacted"
    RESOLVED = "RESOLVED", "Resolved"


class ContactEnquiry(models.Model):
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    subject = models.CharField(max_length=200, blank=True)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=EnquiryStatus.choices, default=EnquiryStatus.NEW)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Contact enquiries"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} — {self.subject or 'General enquiry'}"
