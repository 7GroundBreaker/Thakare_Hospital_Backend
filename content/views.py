from rest_framework import generics, viewsets
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from hospital.models import Doctor, Speciality
from hospital.serializers import DoctorMiniSerializer, SpecialityListSerializer
from hospital.notifications import NotificationService

from .models import Article, ContactEnquiry, FAQ, GalleryImage, Testimonial
from .serializers import (
    ArticleDetailSerializer,
    ArticleListSerializer,
    ContactEnquirySerializer,
    FAQSerializer,
    GalleryImageSerializer,
    TestimonialSerializer,
)


class ArticleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Article.objects.filter(is_published=True).select_related("category", "speciality")
    lookup_field = "slug"
    filterset_fields = ["category__slug", "speciality__slug", "tags"]
    search_fields = ["title", "short_description", "content", "tags"]
    ordering_fields = ["publish_date"]

    def get_serializer_class(self):
        if self.action == "list":
            return ArticleListSerializer
        return ArticleDetailSerializer


class FAQViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = FAQ.objects.filter(is_published=True)
    serializer_class = FAQSerializer
    filterset_fields = ["category", "speciality__slug"]
    search_fields = ["question", "answer"]


class TestimonialViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Testimonial.objects.filter(is_published=True, consent_confirmed=True)
    serializer_class = TestimonialSerializer
    filterset_fields = ["speciality__slug", "doctor__slug"]


class GalleryImageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = GalleryImage.objects.filter(is_active=True).select_related("category")
    serializer_class = GalleryImageSerializer
    filterset_fields = ["category__slug", "is_featured"]


class ContactSubmitThrottle(AnonRateThrottle):
    scope = "contact_submit"


class ContactEnquiryCreateView(generics.CreateAPIView):
    """Public contact-form submission (section 20). No list/retrieve is
    exposed publicly — enquiries are managed via the Django admin."""

    queryset = ContactEnquiry.objects.all()
    serializer_class = ContactEnquirySerializer
    throttle_classes = [ContactSubmitThrottle]

    def perform_create(self, serializer):
        enquiry = serializer.save()
        NotificationService.notify_contact_enquiry(enquiry)


class SearchView(APIView):
    """Global search across doctors, specialities, services and articles
    (section 46). Read-only, public, lightweight — not a full-text engine."""

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        if not query or len(query) < 2:
            return Response({"doctors": [], "specialities": [], "articles": [], "faqs": []})

        doctors = Doctor.objects.filter(is_active=True, full_name__icontains=query)[:5]
        specialities = Speciality.objects.filter(is_active=True, name__icontains=query)[:5]
        articles = Article.objects.filter(is_published=True, title__icontains=query)[:5]
        faqs = FAQ.objects.filter(is_published=True, question__icontains=query)[:5]

        return Response(
            {
                "doctors": DoctorMiniSerializer(doctors, many=True).data,
                "specialities": SpecialityListSerializer(specialities, many=True).data,
                "articles": ArticleListSerializer(articles, many=True).data,
                "faqs": FAQSerializer(faqs, many=True).data,
            }
        )
