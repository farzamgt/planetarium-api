from datetime import datetime
from django.db.models import F, Count
from rest_framework import viewsets, mixins, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from drf_spectacular.utils import extend_schema, OpenApiParameter

from planetarium.models import (
    PlanetariumDome,
    ShowTheme,
    AstronomyShow,
    ShowSession,
    Reservation,
    Ticket,
)
from planetarium.permissions import IsAdminOrIfAuthenticatedReadOnly, IsOwnerOrAdmin
from planetarium.serializers import (
    PlanetariumDomeSerializer,
    ShowThemeSerializer,
    AstronomyShowSerializer,
    ShowSessionSerializer,
    ShowSessionListSerializer,
    ShowSessionDetailSerializer,
    ReservationSerializer,
    ReservationListSerializer,
    TicketSerializer,
    TicketListSerializer,
    TicketSeatsSerializer,
)

from .pagination import StandardResultsSetPagination


class PlanetariumDomeViewSet(mixins.ListModelMixin,
                             mixins.CreateModelMixin,
                             viewsets.GenericViewSet):
    queryset = PlanetariumDome.objects.all().order_by("id")
    serializer_class = PlanetariumDomeSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)
    pagination_class = StandardResultsSetPagination


class ShowThemeViewSet(mixins.ListModelMixin,
                       mixins.CreateModelMixin,
                       viewsets.GenericViewSet):
    queryset = ShowTheme.objects.all().order_by("id")
    serializer_class = ShowThemeSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)
    pagination_class = StandardResultsSetPagination


class AstronomyShowViewSet(mixins.ListModelMixin,
                            mixins.CreateModelMixin,
                            mixins.RetrieveModelMixin,
                            viewsets.GenericViewSet):
    queryset = AstronomyShow.objects.prefetch_related("theme").order_by("id")
    serializer_class = AstronomyShowSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)
    pagination_class = StandardResultsSetPagination

    @staticmethod
    def _params_to_ints(qs):
        """Converts comma-separated string to list of ints"""
        return [int(str_id) for str_id in qs.split(",")]

    def get_queryset(self):
        """Retrieve astronomy shows with optional filters"""
        title = self.request.query_params.get("title")
        theme = self.request.query_params.get("theme")

        queryset = self.queryset

        if title:
            queryset = queryset.filter(title__icontains=title)
        if theme:
            theme_ids = self._params_to_ints(theme)
            queryset = queryset.filter(theme__id__in=theme_ids)

        return queryset.distinct()


class ShowSessionViewSet(viewsets.ModelViewSet):
    queryset = (
        ShowSession.objects.all()
        .select_related("astronomy_show", "planetarium_dome")
        .annotate(
            tickets_available=(
                F("planetarium_dome__rows") * F("planetarium_dome__seats_in_row")
                - Count("tickets")
            )
        ).order_by("id")
    )
    serializer_class = ShowSessionSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        date = self.request.query_params.get("date")
        show_id_str = self.request.query_params.get("show")

        queryset = self.queryset

        if date:
            date = datetime.strptime(date, "%Y-%m-%d").date()
            queryset = queryset.filter(show_time__date=date)

        if show_id_str:
            queryset = queryset.filter(astronomy_show_id=int(show_id_str))

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return ShowSessionListSerializer
        if self.action == "retrieve":
            return ShowSessionDetailSerializer
        return ShowSessionSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="date",
                description="Filter sessions by date in format YYYY-MM-DD",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="show",
                description="Filter sessions by show id",
                required=False,
                type=int,
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        """Get list of show sessions"""
        return super().list(request, *args, **kwargs)


class ReservationPagination(PageNumberPagination):
    page_size = 10
    max_page_size = 100


class ReservationViewSet(mixins.ListModelMixin,
                         mixins.CreateModelMixin,
                         viewsets.GenericViewSet):
    queryset = Reservation.objects.prefetch_related(
        "tickets__show_session__astronomy_show",
        "tickets__show_session__planetarium_dome"
    )
    serializer_class = ReservationSerializer
    pagination_class = ReservationPagination
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Reservation.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return ReservationListSerializer
        return ReservationSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.select_related("show_session")
    serializer_class = TicketSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsOwnerOrAdmin,)

    def get_queryset(self):
        if self.request.user.is_staff:
            return Ticket.objects.all()
        return Ticket.objects.filter(reservation__user=self.request.user)

    def perform_create(self, serializer):
        reservation, _ = Reservation.objects.get_or_create(user=self.request.user)
        serializer.save(reservation=reservation)
