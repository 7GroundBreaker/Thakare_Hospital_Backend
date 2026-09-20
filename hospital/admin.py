from django.contrib import admin

from .models import (
    ConditionTreated,
    Doctor,
    DoctorLeave,
    DoctorSchedule,
    Service,
    SiteSettings,
    Speciality,
)


class ConditionTreatedInline(admin.TabularInline):
    model = ConditionTreated
    extra = 1


class ServiceInline(admin.TabularInline):
    model = Service
    extra = 1
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Speciality)
class SpecialityAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "display_order")
    list_editable = ("is_active", "display_order")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "short_description")
    inlines = [ConditionTreatedInline, ServiceInline]
    fieldsets = (
        (None, {"fields": ("name", "slug", "icon", "is_active", "display_order")}),
        ("Content", {"fields": ("short_description", "description", "when_to_consult")}),
        ("Images", {"fields": ("hero_image", "card_image")}),
        ("SEO", {"fields": ("seo_title", "seo_description", "canonical_url", "og_image")}),
    )


class DoctorScheduleInline(admin.TabularInline):
    model = DoctorSchedule
    extra = 1


class DoctorLeaveInline(admin.TabularInline):
    model = DoctorLeave
    extra = 0


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ("full_name", "designation", "specialities_list", "is_active", "booking_enabled", "display_order")
    list_editable = ("is_active", "booking_enabled", "display_order")
    list_filter = ("specialities", "is_active", "booking_enabled")
    search_fields = ("full_name", "designation")
    prepopulated_fields = {"slug": ("full_name",)}
    filter_horizontal = ("specialities",)
    inlines = [DoctorScheduleInline, DoctorLeaveInline]
    fieldsets = (
        (None, {"fields": ("full_name", "slug", "profile_photo", "designation", "specialities", "sub_speciality")}),
        (
            "Credentials (TODO: leave blank until confirmed by the hospital)",
            {"fields": ("qualification", "experience", "consultation_fee")},
        ),
        ("Profile content", {"fields": ("biography", "areas_of_expertise", "languages")}),
        (
            "Consultation",
            {"fields": ("consultation_timings_note", "clinic_location", "phone", "whatsapp", "booking_enabled")},
        ),
        ("Display", {"fields": ("display_order", "is_active")}),
        ("SEO", {"fields": ("seo_title", "seo_description", "canonical_url", "og_image")}),
    )

    @admin.display(description="Specialities")
    def specialities_list(self, obj):
        return ", ".join(s.name for s in obj.specialities.all())


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Branding", {"fields": ("hospital_name", "tagline", "logo", "favicon")}),
        ("Contact", {"fields": ("phone", "whatsapp_number", "whatsapp_message_template", "email", "address")}),
        ("Map", {"fields": ("google_maps_url", "latitude", "longitude")}),
        ("Hours", {"fields": ("opening_hours",)}),
        (
            "Social & reviews",
            {"fields": ("facebook_url", "instagram_url", "youtube_url", "twitter_url", "linkedin_url", "google_review_url")},
        ),
        (
            "Emergency",
            {"fields": ("emergency_enabled", "emergency_phone", "emergency_availability", "emergency_message")},
        ),
        ("Legal", {"fields": ("privacy_policy", "terms_and_conditions", "medical_disclaimer")}),
        ("Footer", {"fields": ("footer_description",)}),
        ("Analytics", {"fields": ("google_analytics_id", "google_tag_manager_id")}),
        ("AI assistant", {"fields": ("ai_assistant_enabled",)}),
    )

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
