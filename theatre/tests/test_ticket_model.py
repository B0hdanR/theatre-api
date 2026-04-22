from django.contrib.auth import get_user_model
from django.test import TestCase
from django.core.exceptions import ValidationError

from rest_framework.test import APIClient

from theatre.models import Performance, Reservation, TheatreHall, Play, Ticket


def sample_play(**params) -> Play:
    defaults = {
        "title": "Sample play",
        "description": "Sample description",
    }
    defaults.update(params)

    return Play.objects.create(**defaults)

def sample_theatre_hall(**params):
    defaults = {"name": "First", "rows": 20, "seats_in_row": 40}
    defaults.update(params)

    return TheatreHall.objects.create(**defaults)

def sample_performance(**params):
    play = sample_play()
    theatre_hall = sample_theatre_hall()

    defaults = {
        "play": play,
        "theatre_hall": theatre_hall,
        "show_time": "2025-12-15T18:00:00Z",
    }
    defaults.update(params)

    return Performance.objects.create(**defaults)

def sample_reservation(user, **params):
    defaults = {}
    defaults.update(params)

    return Reservation.objects.create(user=user, **defaults)


class TicketModelTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com", password="testpassword123"
        )
        self.client.force_authenticate(self.user)

    def test_create_ticket_successful(self):
        performance = sample_performance()
        reservation = sample_reservation(self.user)

        ticket = Ticket.objects.create(
            performance=performance,
            reservation=reservation,
            row=1,
            seat=1,
        )

        self.assertEqual(str(ticket), f"{performance} (row: 1, seat: 1)")

    def test_create_ticket_with_wrong_seat(self):
        performance = sample_performance()
        reservation = sample_reservation(self.user)
        with self.assertRaises(ValidationError):
            Ticket.objects.create(
                performance=performance,
                reservation=reservation,
                row=1,
                seat=1000,
            )

    def test_create_ticket_with_wrong_row(self):
        performance = sample_performance()
        reservation = sample_reservation(self.user)
        with self.assertRaises(ValidationError):
            Ticket.objects.create(
                performance=performance,
                reservation=reservation,
                row=1000,
                seat=1,
            )

    def test_ticket_is_unique(self):
        performance = sample_performance()
        reservation = sample_reservation(self.user)
        Ticket.objects.create(
            performance=performance,
            reservation=reservation,
            row=1,
            seat=1,
        )

        with self.assertRaises(Exception):
            Ticket.objects.create(
                performance=performance,
                reservation=reservation,
                row=1000,
                seat=1,
            )
