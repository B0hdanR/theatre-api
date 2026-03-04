from drf_spectacular.utils import extend_schema
from rest_framework import viewsets

from theatre.filters import PlayFilter
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
    ReservationSerializer,
)


class TheatreHallViewSet(viewsets.ModelViewSet):
    queryset = TheatreHall.objects.all()
    serializer_class = TheatreHallSerializer


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer


@extend_schema(
    tags=["Plays"],
)
class PlayViewSet(viewsets.ModelViewSet):
    """
    PlayViewSet for Play model.
    Filtering, searching, and ordering can be used
    """
    queryset = Play.objects.prefetch_related("genres", "actors")
    serializer_class = PlaySerializer
    filterset_class = PlayFilter
    search_fields = ["title", "genres__name", "actors__first_name", "actors__last_name", "description"]
    ordering_fields = ["title"]

    def get_serializer_class(self):
        if self.action == "list":
            return PlayListSerializer

        if self.action == "retrieve":
            return PlayDetailSerializer

        return PlaySerializer

    def get_queryset(self):
        return super().get_queryset().distinct()


class PerformanceViewSet(viewsets.ModelViewSet):
    queryset = Performance.objects.select_related("play", "theatre_hall")
    serializer_class = PerformanceSerializer


class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.prefetch_related(
        "tickets__performance__play", "tickets__performance__theatre_hall"
    )
    serializer_class = ReservationSerializer

    def get_queryset(self):
        return Reservation.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
