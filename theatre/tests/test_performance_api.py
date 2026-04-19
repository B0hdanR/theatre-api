from django.contrib.auth import get_user_model
from django.db.models import F, Count
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from theatre.models import Performance, Play, TheatreHall, Ticket, Reservation
from theatre.serializers import PerformanceListSerializer, PerformanceDetailSerializer

PERFORMANCE_URL = reverse("theatre:performance-list")

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

def detail_url(performance_id):
    return reverse("theatre:performance-detail", args=[performance_id])


class UnauthenticatedPerformanceAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_performance_list_allowed(self):
        sample_performance()
        res = self.client.get(PERFORMANCE_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_performance_detail_allowed(self):
        performance = sample_performance()
        res = self.client.get(detail_url(performance.id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_performance_create_forbidden(self):
        play = sample_play()
        theatre_hall = sample_theatre_hall()
        payload = {
            "play": play,
            "theate_hall": theatre_hall,
            "show_time": "2025-11-21T11:00:00Z"
        }
        res = self.client.post(PERFORMANCE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedPerformanceAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com", password="testpassword123"
        )
        self.client.force_authenticate(self.user)

    def test_performance_list(self):
        sample_performance()
        sample_performance()

        res = self.client.get(PERFORMANCE_URL)
        performances = (
            Performance.objects
            .select_related("play", "theatre_hall")
            .annotate(tickets_available=(
                    F("theatre_hall__rows") * F("theatre_hall__seats_in_row")
                    - Count("tickets", distinct=True)
                )
            )
        )
        serializer = PerformanceListSerializer(performances, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_performance_detail(self):
        performance = sample_performance()

        res = self.client.get(detail_url(performance.id))

        serializer = PerformanceDetailSerializer(performance)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_filter_performances_by_plays(self):
        play_1 = sample_play(title="Play1")
        play_2= sample_play(title="Play2")

        sample_performance(play=play_1)
        sample_performance(play=play_2)

        res = self.client.get(
            PERFORMANCE_URL,
            {"play": play_1.id},
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 1)

    def test_filter_performances_by_date_from(self):
        sample_performance(show_time="2025-11-15T18:00:00Z")
        sample_performance(show_time="2025-08-15T18:00:00Z")

        res = self.client.get(
            PERFORMANCE_URL,
            {"date_from": "2025-10-15"},
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 1)

    def test_filter_performances_by_date_to(self):
        sample_performance(show_time="2025-11-15T18:00:00Z")
        sample_performance(show_time="2025-08-15T18:00:00Z")

        res = self.client.get(
            PERFORMANCE_URL,
            {"date_to": "2025-10-15"},
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 1)

    def test_filter_performances_by_play_and_date_from(self):
        play_1 = sample_play(title="Play1")
        play_2 = sample_play(title="Play2")

        sample_performance(play=play_1, show_time="2025-11-15T18:00:00Z")
        sample_performance(play=play_1, show_time="2025-08-15T18:00:00Z")
        sample_performance(play=play_2, show_time="2025-11-15T21:00:00Z")

        res = self.client.get(
            PERFORMANCE_URL,
            {
                "play": play_1.id,
                "date_from": "2025-10-15"
            },
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 1)

    def test_search_performance(self):
        play_1 = sample_play(title="Poppy")
        play_2 = sample_play(title="Dog")
        sample_performance(play=play_1)
        sample_performance(play=play_2)

        res = self.client.get(PERFORMANCE_URL, {"search": "popp"})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 1)

    def test_ordering_performance(self):
        sample_performance(show_time="2025-11-15T18:00:00Z")
        sample_performance(show_time="2025-08-15T18:00:00Z")

        res = self.client.get(PERFORMANCE_URL, {"ordering": "show_time"})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"][0]["show_time"], "2025-08-15T18:00:00Z")


class AdminPerformanceAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="admin@test.test", password="testadmin123", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_performance_successful(self):
        play = sample_play()
        theatre_hall = sample_theatre_hall()
        payload = {
            "play": play.id,
            "theatre_hall": theatre_hall.id,
            "show_time": "2025-11-21T11:00:00Z"
        }

        res = self.client.post(PERFORMANCE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        performance = Performance.objects.get(id=res.data["id"])

        self.assertEqual(performance.play.id, play.id)
        self.assertEqual(performance.theatre_hall.id, theatre_hall.id)

    def test_update_performance_successful(self):
        play = sample_play(title = "New")
        performance = sample_performance()

        res = self.client.patch(
            detail_url(performance.id),
            {"play": play.id},
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        performance.refresh_from_db()
        self.assertEqual(performance.play.id, play.id)

    def test_delete_performance_successful(self):
        performance = sample_performance()

        res = self.client.delete(detail_url(performance.id))

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Performance.objects.filter(id=performance.id).exists())

class PerformanceAPITicketsAvailableTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com", password="testpassword123"
        )
        self.client.force_authenticate(self.user)

    def test_tickets_available_without_tickets(self):
        theatre_hall = sample_theatre_hall()
        sample_performance(theatre_hall=theatre_hall)

        res = self.client.get(PERFORMANCE_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"][0]["tickets_available"], 800)

    def test_tickets_available_with_tickets(self):
        theatre_hall = sample_theatre_hall()
        performance = sample_performance(theatre_hall=theatre_hall)

        reservation = sample_reservation(self.user)

        Ticket.objects.create(
            performance=performance,
            reservation=reservation,
            row=1,
            seat=1
        )
        Ticket.objects.create(
            performance=performance,
            reservation=reservation,
            row=1,
            seat=2
        )

        res = self.client.get(PERFORMANCE_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"][0]["tickets_available"], 798)
