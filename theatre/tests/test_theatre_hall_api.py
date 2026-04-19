from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from theatre.models import TheatreHall
from theatre.serializers import TheatreHallSerializer

THEATRE_HALL_URL = reverse("theatre:theatrehall-list")

def sample_theatre_hall(**params):
    defaults = {"name": "First", "rows": 20, "seats_in_row": 40}
    defaults.update(params)

    return TheatreHall.objects.create(**defaults)

def detail_url(theatrehall_id):
    return reverse("theatre:theatrehall-detail", args=[theatrehall_id])


class UnauthenticatedTheatreHallAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_theatrehall_list_allowed(self):
        sample_theatre_hall()
        res = self.client.get(THEATRE_HALL_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_theatrehall_detail_allowed(self):
        theatrehall = sample_theatre_hall()
        res = self.client.get(detail_url(theatrehall.id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_theatrehall_create_forbidden(self):
        payload = {"name": "None", "rows": 100, "seats_in_row": 200}
        res = self.client.post(THEATRE_HALL_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_capacity_properly(self):
        theatrehall = sample_theatre_hall()

        serializer = TheatreHallSerializer(theatrehall)

        self.assertEqual(serializer.data["capacity"], 800)


class AuthenticatedtheatrehallAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com", password="testpassword123"
        )
        self.client.force_authenticate(self.user)

    def test_theatrehall_list(self):
        sample_theatre_hall()
        sample_theatre_hall(name="Second")

        res = self.client.get(THEATRE_HALL_URL)
        theatrehalls = TheatreHall.objects.all()
        serializer = TheatreHallSerializer(theatrehalls, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_search_theatrehall(self):
        theatrehall = sample_theatre_hall(name="Arctic")
        sample_theatre_hall()

        res = self.client.get(THEATRE_HALL_URL, {"search": "arc"})

        serializer = TheatreHallSerializer(theatrehall)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer.data, res.data["results"])

    def test_ordering_theatrehall(self):
        sample_theatre_hall(name="Arctic")
        sample_theatre_hall()

        res = self.client.get(THEATRE_HALL_URL, {"ordering": "name"})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"][0]["name"], "Arctic")


class AdmintheatrehallAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="admin@test.test", password="testadmin123", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_theatrehall_successful(self):
        payload = {"name": "Bool", "rows": 100, "seats_in_row": 200}

        res = self.client.post(THEATRE_HALL_URL, payload)

        theatrehall = TheatreHall.objects.get(id=res.data["id"])

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(theatrehall.capacity, 20000)

        for key in payload:
            self.assertEqual(payload[key], getattr(theatrehall, key))

    def test_update_theatrehall_successful(self):
        theatrehall = sample_theatre_hall()

        res = self.client.patch(
            detail_url(theatrehall.id),
            {"rows": 50},
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        theatrehall.refresh_from_db()
        self.assertEqual(theatrehall.rows, 50)

    def test_delete_theatrehall_successful(self):
        theatrehall = sample_theatre_hall()

        res = self.client.delete(detail_url(theatrehall.id))

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(TheatreHall.objects.filter(id=theatrehall.id).exists())
