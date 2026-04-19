from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from theatre.models import Actor
from theatre.serializers import ActorSerializer

ACTOR_URL = reverse("theatre:actor-list")

def sample_actor(**params):
    defaults = {"first_name": "Lisa", "last_name": "Nolan"}
    defaults.update(params)

    return Actor.objects.create(**defaults)

def detail_url(actor_id):
    return reverse("theatre:actor-detail", args=[actor_id])


class UnauthenticatedActorAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_actor_list_allowed(self):
        sample_actor()
        res = self.client.get(ACTOR_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_actor_detail_allowed(self):
        actor = sample_actor()
        res = self.client.get(detail_url(actor.id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_actor_create_forbidden(self):
        payload = {"first_name": "Bart", "last_name": "Hill"}
        res = self.client.post(ACTOR_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedActorAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com", password="testpassword123"
        )
        self.client.force_authenticate(self.user)

    def test_actor_list(self):
        sample_actor()
        sample_actor(first_name="Bart", last_name="Nolan")

        res = self.client.get(ACTOR_URL)
        actors = Actor.objects.all()
        serializer = ActorSerializer(actors, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_search_actor(self):
        actor = sample_actor(first_name="Bart", last_name="Nolan")
        sample_actor()

        res = self.client.get(ACTOR_URL, {"search": "bar"})

        serializer = ActorSerializer(actor)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer.data, res.data["results"])

    def test_ordering_actor(self):
        sample_actor(first_name="Bart", last_name="Nolan")
        sample_actor()

        res = self.client.get(ACTOR_URL, {"ordering": "first_name"})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"][0]["first_name"], "Bart")


class AdminActorAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="admin@test.test", password="testadmin123", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_actor_successful(self):
        payload = {"first_name": "Bart", "last_name": "Hill"}

        res = self.client.post(ACTOR_URL, payload)

        actor = Actor.objects.get(id=res.data["id"])

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        for key in payload:
            self.assertEqual(payload[key], getattr(actor, key))

    def test_update_actor_successful(self):
        actor = sample_actor()

        res = self.client.patch(
            detail_url(actor.id),
            {"first_name": "Updated First Name"},
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        actor.refresh_from_db()
        self.assertEqual(actor.first_name, "Updated First Name")

    def test_delete_actor_successful(self):
        actor = sample_actor()

        res = self.client.delete(detail_url(actor.id))

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Actor.objects.filter(id=actor.id).exists())
