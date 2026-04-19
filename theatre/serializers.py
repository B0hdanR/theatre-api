from django.db import transaction
from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError

from theatre.models import (
    TheatreHall,
    Actor,
    Genre,
    Play,
    Performance,
    Reservation,
    Ticket,
)


class TheatreHallSerializer(serializers.ModelSerializer):
    class Meta:
        model = TheatreHall
        fields = ("id", "name", "rows", "seats_in_row", "capacity")


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ("id", "name")


class ActorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actor
        fields = ("id", "first_name", "last_name", "full_name")


class PlaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Play
        fields = ("id", "title", "description", "genres", "actors")


class PlayListSerializer(PlaySerializer):
    genres = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="name"
    )
    actors = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="full_name"
    )


class PlayDetailSerializer(PlaySerializer):
    genres = GenreSerializer(many=True, read_only=True)
    actors = ActorSerializer(many=True, read_only=True)


class PerformanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Performance
        fields = ("id", "play", "theatre_hall", "show_time")


class PerformanceListSerializer(serializers.ModelSerializer):
    play_title = serializers.CharField(source="play.title", read_only=True)
    theatre_hall_name = serializers.CharField(
        source="theatre_hall.name", read_only=True
    )
    theatre_hall_capacity = serializers.IntegerField(
        source="theatre_hall.capacity", read_only=True
    )
    tickets_available = serializers.IntegerField(read_only=True)

    class Meta:
        model = Performance
        fields = (
            "id",
            "play_title",
            "theatre_hall_name",
            "theatre_hall_capacity",
            "tickets_available",
            "show_time"
        )


class TicketSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        try:
            Ticket.validate_ticket(
                attrs["row"],
                attrs["seat"],
                attrs["performance"].theatre_hall,
                DjangoValidationError
            )
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict)

        return attrs

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "performance")


class TicketListSerializer(TicketSerializer):
    performance = PerformanceListSerializer(many=False, read_only=True)


class TakenSeatsSerializer(TicketSerializer):
    class Meta:
        model = Ticket
        fields = ("row", "seat")


class PerformanceDetailSerializer(PerformanceSerializer):
    play = PlayListSerializer(many=False, read_only=True)
    theatre_hall = TheatreHallSerializer(many=False, read_only=True)
    taken_seats = TakenSeatsSerializer(source="tickets", many=True, read_only=True)

    class Meta:
        model = Performance
        fields = ("id", "play", "theatre_hall", "taken_seats", "show_time")


class ReservationSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, allow_empty=False)

    class Meta:
        model = Reservation
        fields = ("id", "tickets", "created_at")

    def create(self, validated_data):
        with transaction.atomic():
            tickets = validated_data.pop("tickets")
            reservation = Reservation.objects.create(**validated_data)

            for ticket in tickets:
                Ticket.objects.create(reservation=reservation, **ticket)

            return reservation

    def validate(self, attrs):
        tickets = attrs.get("tickets")

        taken = set()
        for ticket in tickets:
            key = (ticket["row"], ticket["seat"], ticket["performance"])

            if key in taken:
                raise serializers.ValidationError(
                    "Ticket with same row and seat already exists"
                )
            taken.add(key)

        return attrs


class ReservationDetailSerializer(ReservationSerializer):
    tickets = TicketListSerializer(many=True, read_only=True)
