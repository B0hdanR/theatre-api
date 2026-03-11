from django.db.models import Count, F
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter

from theatre.filters import PlayFilter, PerformanceFilter
from theatre.models import (
    TheatreHall,
    Actor,
    Genre,
    Play,
    Performance,
    Reservation
)
from theatre.serializers import (
    TheatreHallSerializer,
    ActorSerializer,
    GenreSerializer,
    PlaySerializer,
    PlayDetailSerializer,
    PlayListSerializer,
    PerformanceSerializer,
    PerformanceListSerializer,
    PerformanceDetailSerializer,
    ReservationSerializer,
    ReservationDetailSerializer,
)


@extend_schema(
    tags=["Theatre Halls"],
    description="API endpoint for viewing theatre halls.",
    parameters=[
        OpenApiParameter(
            "ordering",
            type=OpenApiTypes.STR,
            required=False,
            description="Which field to use when ordering the results.",
            enum=["name", "-name"]
        ),
        OpenApiParameter(
            "search",
            description="Search by Theatre hall name",
        )
    ]
)
class TheatreHallViewSet(viewsets.ModelViewSet):
    """
    TheatreHallViewSet for TheatreHall model.
    """
    queryset = TheatreHall.objects.all()
    serializer_class = TheatreHallSerializer
    search_fields = ["name"]
    ordering_fields = ["name"]


@extend_schema(
    tags=["Genres"],
    description="API endpoint for viewing genres.",
    parameters=[
        OpenApiParameter(
            "ordering",
            type=OpenApiTypes.STR,
            required=False,
            description="Which field to use when ordering the results.",
            enum=["name", "-name"]
        ),
        OpenApiParameter(
            "search",
            description="Search by genre name",
        )
    ]
)
class GenreViewSet(viewsets.ModelViewSet):
    """
    GenreViewSet for Genre model.
    """

    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    search_fields = ["name"]
    ordering_fields = ["name"]


@extend_schema(
    tags=["Actors"],
    description="API endpoint for viewing actors.",
    parameters=[
        OpenApiParameter(
            "ordering",
            type=OpenApiTypes.STR,
            required=False,
            description="Which field to use when ordering the results.",
            enum=["first_name", "-first_name", "last_name", "-last_name"]
        ),
        OpenApiParameter(
            "search",
            description="Search by actor's first or last name",
        )
    ]
)
class ActorViewSet(viewsets.ModelViewSet):
    """
    ActorViewSet for Actor model.
    """
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer
    search_fields = ["first_name", "last_name"]
    ordering_fields = ["first_name", "last_name"]


@extend_schema(
    tags=["Plays"],
    description="API endpoint for viewing theatre plays.",
    parameters=[
        OpenApiParameter(
            "ordering",
            type=OpenApiTypes.STR,
            required=False,
            description="Which field to use when ordering the results.",
            enum=["title", "-title"]
        ),
        OpenApiParameter(
            "search",
            description="Search by actor's first or last name, "
                        "genre name, play title or description",
        )
    ]
)
class PlayViewSet(viewsets.ModelViewSet):
    """
    PlayViewSet for Play model.
    Filtering, searching, and ordering can be used.
    """
    queryset = Play.objects.prefetch_related("genres", "actors")
    serializer_class = PlaySerializer
    filterset_class = PlayFilter
    search_fields = [
        "title",
        "genres__name",
        "actors__first_name",
        "actors__last_name",
        "description"
    ]
    ordering_fields = ["title"]

    def get_serializer_class(self):
        if self.action == "list":
            return PlayListSerializer

        if self.action == "retrieve":
            return PlayDetailSerializer

        return PlaySerializer

    def get_queryset(self):
        return super().get_queryset().distinct()


@extend_schema(
    tags=["Performances"],
    description="API endpoint for viewing performances.",
    parameters=[
        OpenApiParameter(
            "ordering",
            type=OpenApiTypes.STR,
            required=False,
            description="Which field to use when ordering the results.",
            enum=["show_time", "-show_time"]
        ),
        OpenApiParameter(
            "search",
            description="Search by theatre hall name or play title",
        )
    ]
)
class PerformanceViewSet(viewsets.ModelViewSet):
    """
    PerformanceViewSet for Performance model.
    """
    queryset = (
        Performance.objects.
        select_related("play", "theatre_hall")
        .annotate(
            tickets_available = (
                F("theatre_hall__rows") * F("theatre_hall__seats_in_row")
                - Count("tickets")
            )
        )
    )
    serializer_class = PerformanceSerializer
    filterset_class = PerformanceFilter
    search_fields = ["play__title", "theatre_hall__name"]
    ordering_fields = ["show_time"]

    def get_serializer_class(self):
        if self.action == "list":
            return PerformanceListSerializer
        if self.action == "retrieve":
            return PerformanceDetailSerializer

        return PerformanceSerializer


@extend_schema(
    tags=["Reservations"],
    description="API endpoint for viewing reservations.",
    parameters=[
        OpenApiParameter(
            "ordering",
            type=OpenApiTypes.STR,
            required=False,
            description="Which field to use when ordering the results.",
            enum=["created_at", "-created_at"]
        ),
    ]
)
class ReservationViewSet(viewsets.ModelViewSet):
    """
    ReservationViewSet for Reservation model.
    """
    queryset = Reservation.objects.prefetch_related(
        "tickets__performance__play", "tickets__performance__theatre_hall"
    )
    serializer_class = ReservationSerializer
    filter_backends = [
        DjangoFilterBackend,
        OrderingFilter,
    ]
    ordering_fields = ["created_at"]

    def get_queryset(self):
        return Reservation.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ReservationDetailSerializer

        return ReservationSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
