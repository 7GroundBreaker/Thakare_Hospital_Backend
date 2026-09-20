from rest_framework.routers import DefaultRouter

from .views import DoctorViewSet, ServiceViewSet, SpecialityViewSet

router = DefaultRouter()
router.register("doctors", DoctorViewSet, basename="doctor")
router.register("specialities", SpecialityViewSet, basename="speciality")
router.register("services", ServiceViewSet, basename="service")

urlpatterns = router.urls
