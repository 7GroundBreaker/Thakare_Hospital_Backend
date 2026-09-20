from rest_framework import serializers

from .models import ConditionTreated, Doctor, DoctorSchedule, Service, SiteSettings, Speciality


class ConditionTreatedSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConditionTreated
        fields = ("id", "name", "description")


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ("id", "name", "slug", "description", "icon", "display_order")


class SpecialityListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Speciality
        fields = (
            "id",
            "name",
            "slug",
            "short_description",
            "icon",
            "card_image",
            "display_order",
        )


class DoctorMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = (
            "id",
            "full_name",
            "slug",
            "profile_photo",
            "designation",
            "sub_speciality",
        )


class SpecialityDetailSerializer(serializers.ModelSerializer):
    conditions_treated = ConditionTreatedSerializer(many=True, read_only=True)
    services = ServiceSerializer(many=True, read_only=True)
    doctors = DoctorMiniSerializer(many=True, read_only=True)

    class Meta:
        model = Speciality
        fields = (
            "id",
            "name",
            "slug",
            "short_description",
            "description",
            "when_to_consult",
            "icon",
            "hero_image",
            "card_image",
            "conditions_treated",
            "services",
            "doctors",
            "seo_title",
            "seo_description",
            "canonical_url",
            "og_image",
        )


class DoctorScheduleSerializer(serializers.ModelSerializer):
    day_of_week_display = serializers.CharField(source="get_day_of_week_display", read_only=True)

    class Meta:
        model = DoctorSchedule
        fields = (
            "day_of_week",
            "day_of_week_display",
            "start_time",
            "end_time",
            "break_start",
            "break_end",
            "slot_duration_minutes",
        )


class DoctorListSerializer(serializers.ModelSerializer):
    specialities = SpecialityListSerializer(many=True, read_only=True)

    class Meta:
        model = Doctor
        fields = (
            "id",
            "full_name",
            "slug",
            "profile_photo",
            "designation",
            "specialities",
            "biography",
            "consultation_timings_note",
            "clinic_location",
            "booking_enabled",
        )


class DoctorDetailSerializer(serializers.ModelSerializer):
    specialities = SpecialityListSerializer(many=True, read_only=True)
    schedules = DoctorScheduleSerializer(many=True, read_only=True)
    expertise_list = serializers.ListField(child=serializers.CharField(), read_only=True)
    language_list = serializers.ListField(child=serializers.CharField(), read_only=True)

    class Meta:
        model = Doctor
        fields = (
            "id",
            "full_name",
            "slug",
            "profile_photo",
            "designation",
            "qualification",
            "specialities",
            "sub_speciality",
            "biography",
            "experience",
            "expertise_list",
            "language_list",
            "consultation_fee",
            "consultation_timings_note",
            "clinic_location",
            "phone",
            "whatsapp",
            "booking_enabled",
            "schedules",
            "seo_title",
            "seo_description",
            "canonical_url",
            "og_image",
        )


class SiteSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSettings
        fields = (
            "hospital_name",
            "logo",
            "favicon",
            "hero_image",
            "about_image",
            "tagline",
            "phone",
            "whatsapp_number",
            "whatsapp_message_template",
            "email",
            "address",
            "google_maps_url",
            "latitude",
            "longitude",
            "opening_hours",
            "facebook_url",
            "instagram_url",
            "youtube_url",
            "twitter_url",
            "linkedin_url",
            "google_review_url",
            "emergency_enabled",
            "emergency_phone",
            "emergency_availability",
            "emergency_message",
            "privacy_policy",
            "terms_and_conditions",
            "medical_disclaimer",
            "footer_description",
            "google_analytics_id",
            "google_tag_manager_id",
            "ai_assistant_enabled",
        )
