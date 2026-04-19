from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from theatre.models import Reservation, Play, TheatreHall, Performance, Ticket
from theatre.serializers import ReservationSerializer, ReservationDetailSerializer

RESERVATION_URL = reverse("theatre:reservation-list")

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

def detail_url(reservation_id):
    return reverse("theatre:reservation-detail", args=[reservation_id])


class UnauthenticatedReservationAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_reservation_auth_required(self):
        res = self.client.post(RESERVATION_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_can_not_create_reservation(self):
        performance = sample_performance()

        payload = {
            "tickets": [
                {"row": 1, "seat": 1, "performance": performance.id},
                {"row": 1, "seat": 2, "performance": performance.id},
            ]
        }

        res = self.client.post(RESERVATION_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedReservationAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com", password="testpassword123"
        )
        self.client.force_authenticate(self.user)

    def test_reservation_list(self):
        sample_reservation(user=self.user)

        res = self.client.get(RESERVATION_URL)
        reservations = Reservation.objects.filter(user=self.user)
        serializer = ReservationSerializer(reservations, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_reservation_detail(self):
        reservation = sample_reservation(user=self.user)
        performance = sample_performance()

        Ticket.objects.create(
            performance=performance,
            reservation=reservation,
            row=1,
            seat=1,
        )

        res = self.client.get(detail_url(reservation.id))

        serializer = ReservationDetailSerializer(reservation)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
        self.assertEqual(len(res.data["tickets"]), 1)

    def test_create_reservation(self):
        performance = sample_performance()

        payload = {
            "tickets": [
                {"row": 1, "seat": 1, "performance": performance.id},
                {"row": 1, "seat": 2, "performance": performance.id},
            ]
        }

        res = self.client.post(RESERVATION_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Reservation.objects.count(), 1)
        self.assertEqual(Ticket.objects.count(), 2)

    def test_can_not_see_other_user_reservations(self):
        user_2 = get_user_model().objects.create_user(
            email="test1@test.com", password="testpassword1231"
        )

        sample_reservation(user=self.user)
        reservation = sample_reservation(user=user_2)

        res = self.client.get(detail_url(reservation.id))

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_reservation_user_automatically_assigned(self):
        performance = sample_performance()

        payload = {
            "tickets": [
                {"row": 1, "seat": 1, "performance": performance.id},
                {"row": 1, "seat": 2, "performance": performance.id},
            ]
        }

        res = self.client.post(RESERVATION_URL, payload, format="json")
        reservation = Reservation.objects.get(id=res.data["id"])

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(reservation.user, self.user)

    def test_can_not_create_reservation_without_tickets(self):
        payload = {
            "tickets": []
        }

        res = self.client.post(RESERVATION_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_can_not_create_reservation_with_taken_seats(self):
        performance = sample_performance()
        reservation = sample_reservation(user=self.user)

        Ticket.objects.create(
            performance=performance,
            reservation=reservation,
            row=1,
            seat=1,
        )

        payload = {
            "tickets": [
                {"row": 1, "seat": 1, "performance": performance.id},
                {"row": 1, "seat": 2, "performance": performance.id},
            ]
        }

        res = self.client.post(RESERVATION_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_can_not_create_reservation_with_the_same_seats(self):
        performance = sample_performance()

        payload = {
            "tickets": [
                {"row": 1, "seat": 1, "performance": performance.id},
                {"row": 1, "seat": 1, "performance": performance.id},
            ]
        }

        res = self.client.post(RESERVATION_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_can_not_create_reservation_with_wrong_ticket(self):
        performance = sample_performance()

        payload = {
            "tickets": [
                {"row": 1000, "seat": 1, "performance": performance.id},
            ]
        }

        res = self.client.post(RESERVATION_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
