from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Doctor, Service, SiteSettings, Speciality
from .serializers import (
    DoctorDetailSerializer,
    DoctorListSerializer,
    ServiceSerializer,
    SiteSettingsSerializer,
    SpecialityDetailSerializer,
    SpecialityListSerializer,
)


class SpecialityViewSet(viewsets.ReadOnlyModelViewSet):
    """Public read-only speciality listing/detail (section 12)."""

    queryset = Speciality.objects.filter(is_active=True).prefetch_related(
        "conditions_treated", "services", "doctors"
    )
    lookup_field = "slug"
    filterset_fields = []
    search_fields = ["name", "short_description"]
    ordering_fields = ["display_order", "name"]

    def get_serializer_class(self):
        if self.action == "list":
            return SpecialityListSerializer
        return SpecialityDetailSerializer


class DoctorViewSet(viewsets.ReadOnlyModelViewSet):
    """Public read-only doctor listing/profile (section 10/11)."""

    queryset = Doctor.objects.filter(is_active=True).prefetch_related("specialities", "schedules")
    lookup_field = "slug"
    filterset_fields = ["specialities__slug"]
    search_fields = ["full_name", "designation"]
    ordering_fields = ["display_order", "full_name"]

    def get_serializer_class(self):
        if self.action == "list":
            return DoctorListSerializer
        return DoctorDetailSerializer


class ServiceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Service.objects.filter(is_active=True).select_related("speciality")
    serializer_class = ServiceSerializer
    filterset_fields = ["speciality__slug"]


class SiteSettingsView(APIView):
    """Public hospital-wide settings (section 34) — read-only."""

    def get(self, request):
        settings_obj = SiteSettings.load()
        return Response(SiteSettingsSerializer(settings_obj).data)
