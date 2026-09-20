from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    ArticleViewSet,
    ContactEnquiryCreateView,
    FAQViewSet,
    GalleryImageViewSet,
    SearchView,
    TestimonialViewSet,
)

router = DefaultRouter()
router.register("articles", ArticleViewSet, basename="article")
router.register("faqs", FAQViewSet, basename="faq")
router.register("testimonials", TestimonialViewSet, basename="testimonial")
router.register("gallery", GalleryImageViewSet, basename="gallery-image")

urlpatterns = [
    path("contact/", ContactEnquiryCreateView.as_view(), name="contact-create"),
    path("search/", SearchView.as_view(), name="search"),
] + router.urls
