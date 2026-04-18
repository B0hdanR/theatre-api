from re import search

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from theatre.models import Genre
from theatre.serializers import GenreSerializer

GENRE_URL = reverse("theatre:genre-list")

def sample_genre(**params):
    defaults = {
        "name": "Comedy",
    }
    defaults.update(params)

    return Genre.objects.create(**defaults)

def detail_url(genre_id):
    return reverse("theatre:genre-detail", args=[genre_id])


class UnauthenticatedGenreAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_genre_list_allowed(self):
        sample_genre()
        res = self.client.get(GENRE_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_genre_detail_allowed(self):
        genre = sample_genre()
        res = self.client.get(detail_url(genre.id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_genre_create_forbidden(self):
        payload = {"name": "Sample genre"}
        res = self.client.post(GENRE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedGenreAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com", password="testpassword123"
        )
        self.client.force_authenticate(self.user)

    def test_genre_list(self):
        sample_genre()
        sample_genre(name="Horror")

        res = self.client.get(GENRE_URL)
        genres = Genre.objects.all()
        serializer = GenreSerializer(genres, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_search_genre(self):
        genre = sample_genre(name="Drama")
        sample_genre()

        res = self.client.get(GENRE_URL, {"search": "dra"})

        serializer = GenreSerializer(genre)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer.data, res.data["results"])

    def test_ordeering_genre(self):
        sample_genre(name="Drama")
        sample_genre()

        res = self.client.get(GENRE_URL, {"ordering": "name"})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"][0]["name"], "Comedy")


class AdminMovieAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="admin@test.test", password="testadmin123", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_genre_successful(self):
        payload = {"name": "Drama"}

        res = self.client.post(GENRE_URL, payload)

        genre = Genre.objects.get(id=res.data["id"])

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        for key in payload:
            self.assertEqual(payload[key], getattr(genre, key))

    def test_update_genre_successful(self):
        genre = sample_genre()

        res = self.client.patch(
            detail_url(genre.id),
            {"name": "Updated Name"},
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        genre.refresh_from_db()
        self.assertEqual(genre.name, "Updated Name")

    def test_delete_genre_successful(self):
        genre = sample_genre()

        res = self.client.delete(detail_url(genre.id))

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Genre.objects.filter(id=genre.id).exists())
