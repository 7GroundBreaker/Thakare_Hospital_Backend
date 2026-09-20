from django.contrib import admin

from .models import (
    Article,
    ArticleCategory,
    ContactEnquiry,
    FAQ,
    GalleryCategory,
    GalleryImage,
    Testimonial,
)


@admin.register(ArticleCategory)
class ArticleCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "display_order")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "speciality", "is_published", "publish_date")
    list_filter = ("category", "speciality", "is_published")
    search_fields = ("title", "short_description", "content", "tags")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("related_articles",)
    fieldsets = (
        (None, {"fields": ("title", "slug", "category", "speciality", "author", "publish_date", "is_published")}),
        ("Content", {"fields": ("featured_image", "short_description", "content", "key_takeaways", "tags")}),
        ("Related", {"fields": ("related_articles",)}),
        ("SEO", {"fields": ("seo_title", "seo_description", "canonical_url", "og_image")}),
    )


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question", "category", "speciality", "display_order", "is_published")
    list_editable = ("display_order", "is_published")
    list_filter = ("category", "is_published")
    search_fields = ("question", "answer")


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ("patient_name", "speciality", "doctor", "rating", "date", "consent_confirmed", "is_published")
    list_filter = ("speciality", "doctor", "is_published", "consent_confirmed")
    search_fields = ("patient_name", "testimonial_text")
    list_editable = ("is_published",)


@admin.register(GalleryCategory)
class GalleryCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "display_order")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display = ("caption", "category", "is_featured", "is_active", "display_order")
    list_editable = ("is_featured", "is_active", "display_order")
    list_filter = ("category", "is_featured", "is_active")


@admin.register(ContactEnquiry)
class ContactEnquiryAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "email", "subject", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("name", "phone", "email", "message")
    list_editable = ("status",)
    readonly_fields = ("created_at",)
