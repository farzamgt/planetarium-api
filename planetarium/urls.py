from django.urls import path
from rest_framework import routers

from planetarium.views import (
    PlanetariumDomeViewSet,
    ShowThemeViewSet,
    AstronomyShowViewSet,
    ShowSessionViewSet,
    ReservationViewSet,
    TicketViewSet,
)

router = routers.DefaultRouter()
router.register("domes", PlanetariumDomeViewSet)
router.register("themes", ShowThemeViewSet)
router.register("shows", AstronomyShowViewSet)
router.register("sessions", ShowSessionViewSet)
router.register("reservations", ReservationViewSet)
router.register("tickets", TicketViewSet)

urlpatterns = router.urls

app_name = "planetarium"
