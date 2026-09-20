from rest_framework import serializers

from .models import (
    Article,
    ArticleCategory,
    ContactEnquiry,
    FAQ,
    GalleryCategory,
    GalleryImage,
    Testimonial,
)


class ArticleCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticleCategory
        fields = ("id", "name", "slug")


class ArticleListSerializer(serializers.ModelSerializer):
    category = ArticleCategorySerializer(read_only=True)

    class Meta:
        model = Article
        fields = (
            "id",
            "title",
            "slug",
            "featured_image",
            "category",
            "author",
            "publish_date",
            "short_description",
            "tags",
        )


class ArticleDetailSerializer(serializers.ModelSerializer):
    category = ArticleCategorySerializer(read_only=True)
    related_articles = ArticleListSerializer(many=True, read_only=True)
    tag_list = serializers.ListField(child=serializers.CharField(), read_only=True)
    takeaway_list = serializers.ListField(child=serializers.CharField(), read_only=True)
    speciality_slug = serializers.CharField(source="speciality.slug", default=None, read_only=True)

    class Meta:
        model = Article
        fields = (
            "id",
            "title",
            "slug",
            "featured_image",
            "category",
            "speciality_slug",
            "author",
            "publish_date",
            "short_description",
            "content",
            "takeaway_list",
            "tag_list",
            "related_articles",
            "seo_title",
            "seo_description",
            "canonical_url",
            "og_image",
        )


class FAQSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source="get_category_display", read_only=True)

    class Meta:
        model = FAQ
        fields = ("id", "question", "answer", "category", "category_display", "display_order")


class TestimonialSerializer(serializers.ModelSerializer):
    speciality_name = serializers.CharField(source="speciality.name", default="", read_only=True)
    doctor_name = serializers.CharField(source="doctor.full_name", default="", read_only=True)

    class Meta:
        model = Testimonial
        fields = (
            "id",
            "patient_name",
            "testimonial_text",
            "speciality_name",
            "doctor_name",
            "photo",
            "rating",
            "date",
        )


class GalleryCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = GalleryCategory
        fields = ("id", "name", "slug")


class GalleryImageSerializer(serializers.ModelSerializer):
    category = GalleryCategorySerializer(read_only=True)

    class Meta:
        model = GalleryImage
        fields = ("id", "category", "image", "caption", "is_featured", "display_order")


class ContactEnquirySerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactEnquiry
        fields = ("name", "phone", "email", "subject", "message")

    def validate(self, attrs):
        if not attrs.get("phone") and not attrs.get("email"):
            raise serializers.ValidationError("Please provide a phone number or an email address.")
        return attrs
