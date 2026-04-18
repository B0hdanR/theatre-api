from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from theatre.models import Play, Genre, Actor, Performance, TheatreHall
from theatre.serializers import PlayListSerializer, PlayDetailSerializer

PLAY_URL = reverse("theatre:play-list")

def detail_url(play_id):
    return reverse("theatre:play-detail", args=[play_id])

def sample_play(**params) -> Play:
    defaults = {
        "title": "Sample play",
        "description": "Sample description",
    }
    defaults.update(params)

    return Play.objects.create(**defaults)

def sample_genre(**params):
    defaults = {
        "name": "Comedy",
    }
    defaults.update(params)

    return Genre.objects.create(**defaults)

def sample_actor(**params):
    defaults = {"first_name": "Lisa", "last_name": "Nolan"}
    defaults.update(params)

    return Actor.objects.create(**defaults)

def sample_performance(**params):
    theatre_hall = TheatreHall.objects.create(
        name="Blue", rows=20, seats_in_row=20
    )

    defaults = {
        "show_time": "2022-06-02 14:00:00",
        "movie": None,
        "cinema_hall": theatre_hall,
    }
    defaults.update(params)

    return Performance.objects.create(**defaults)


class UnauthenticatedPlayAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_play_list_allowed(self):
        sample_play()
        res = self.client.get(PLAY_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_play_detail_allowed(self):
        play = sample_play()
        res = self.client.get(detail_url(play.id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_play_create_forbidden(self):
        payload = {
            "title": "Sample play 1",
            "description": "Sample description 1"
        }
        res = self.client.post(PLAY_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedPlayAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com", password="testpassword123"
        )
        self.client.force_authenticate(self.user)

    def test_play_list(self):
        sample_play()
        sample_play(title="King")

        res = self.client.get(PLAY_URL)
        plays = Play.objects.all()
        serializer = PlayListSerializer(plays, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_play_detail(self):
        play = sample_play()

        play.genres.add(sample_genre())
        play.actors.add(sample_actor())

        res = self.client.get(detail_url(play.id))
        serializer = PlayDetailSerializer(play)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_filter_plays_by_actors(self):
        play_without_actors = sample_play()
        play_with_actor_1 = sample_play(title="Play1")
        play_with_actor_2 = sample_play(title="Play2")

        actor_1 = Actor.objects.create(first_name="Actor1Name", last_name="Actor1LastName")
        actor_2 = Actor.objects.create(first_name="Actor2Name", last_name="Actor2LastName")

        play_with_actor_1.actors.add(actor_1)
        play_with_actor_2.actors.add(actor_2)

        res = self.client.get(
            PLAY_URL,
            {"actors": f"{actor_1.id},{actor_2.id}"},
        )

        serializer_without_actors = PlayListSerializer(play_without_actors)
        serializer_play_with_actor_1 = PlayListSerializer(play_with_actor_1)
        serializer_play_with_actor_2 = PlayListSerializer(play_with_actor_2)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer_play_with_actor_1.data, res.data["results"])
        self.assertIn(serializer_play_with_actor_2.data, res.data["results"])
        self.assertNotIn(serializer_without_actors.data, res.data["results"])
        self.assertEqual(len(res.data["results"]), 2)

    def test_filter_plays_by_genres(self):
        play_without_genres = sample_play()
        play_with_genre_1 = sample_play(title="Play1")
        play_with_genre_2 = sample_play(title="Play2")

        genre_1 = Genre.objects.create(name="Genre1")
        genre_2 = Genre.objects.create(name="Genre2")

        play_with_genre_1.genres.add(genre_1)
        play_with_genre_2.genres.add(genre_2)

        res = self.client.get(
            PLAY_URL,
            {"genres": f"{genre_1.id},{genre_2.id}"},
        )

        serializer_without_genres = PlayListSerializer(play_without_genres)
        serializer_play_with_genre_1 = PlayListSerializer(play_with_genre_1)
        serializer_play_with_genre_2 = PlayListSerializer(play_with_genre_2)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer_play_with_genre_1.data, res.data["results"])
        self.assertIn(serializer_play_with_genre_2.data, res.data["results"])
        self.assertNotIn(serializer_without_genres.data, res.data["results"])
        self.assertEqual(len(res.data["results"]), 2)

    def test_filter_plays_by_title(self):
        play1 = sample_play(title="Play1")
        sample_play(title="Play2")

        res = self.client.get(
            PLAY_URL,
            {"title": f"1"},
        )

        serializer = PlayListSerializer(play1)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer.data, list(res.data["results"]))
        self.assertEqual(len(res.data["results"]), 1)

    def test_filter_plays_by_genre_and_title(self):
        play_with_genre_1 = sample_play(title="Play1")
        play_with_genre_2 = sample_play(title="Play2")
        genre_1 = Genre.objects.create(name="Genre1")
        genre_2 = Genre.objects.create(name="Genre2")
        play_with_genre_1.genres.add(genre_1)
        play_with_genre_2.genres.add(genre_2)

        sample_play(title="Play1")

        res = self.client.get(
            PLAY_URL,
            {"genres": f"{genre_1.id}", "title": f"1"},
        )

        serializer_play_with_genre_1 = PlayListSerializer(play_with_genre_1)
        serializer_play_with_genre_2 = PlayListSerializer(play_with_genre_2)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer_play_with_genre_1.data, res.data["results"])
        self.assertNotIn(serializer_play_with_genre_2.data, res.data["results"])
        self.assertEqual(len(res.data["results"]), 1)

    def test_filter_plays_invalid_genre(self):
        res = self.client.get(
            PLAY_URL,
            {"genres": "1, foo"},
        )

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_plays_invalid_actor(self):
        res = self.client.get(
            PLAY_URL,
            {"actors": "1, foo"},
        )

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_movie_detail(self):
        play = sample_play()
        play.actors.add(Actor.objects.create(first_name="Actor1Name", last_name="Actor1LastName"))

        url = detail_url(play.id)

        res = self.client.get(url)

        serializer = PlayDetailSerializer(play)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_search_play(self):
        play1 = sample_play(title="Play1")
        sample_play(title="Play2")

        res = self.client.get(
            PLAY_URL,
            {"search": "play1"},
        )

        serializer = PlayListSerializer(play1)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer.data, res.data["results"])
        self.assertEqual(len(res.data["results"]), 1)

    def test_ordering_play(self):
        play1 = sample_play(title="Play2")
        play2 = sample_play(title="Play1")

        res = self.client.get(
            PLAY_URL,
            {"ordering": "title"},
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"][0]["title"], play2.title)
        self.assertEqual(res.data["results"][1]["title"], play1.title)

    def test_create_play_forbidden(self):
        payload = {
            "title": "Play",
            "description": "Description",
            "duration": 110,
        }

        res = self.client.post(PLAY_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_play_is_distinct(self):
        play = sample_play(title="Play")
        actor = sample_actor()

        play.actors.add(actor)

        res = self.client.get(
            PLAY_URL,
            {"actors": f"{actor.id}"}
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 1)


class AdminMovieAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="admin@test.test", password="testadmin123", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_play_successful(self):
        payload = {
            "title": "Play",
            "description": "Description",
        }

        res = self.client.post(PLAY_URL, payload)

        play = Play.objects.get(id=res.data["id"])

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        for key in payload:
            self.assertEqual(payload[key], getattr(play, key))

    def test_create_movie_with_actors(self):
        actor_1 = Actor.objects.create(first_name="Actor1Name", last_name="Actor1LastName")
        actor_2 = Actor.objects.create(first_name="Actor2Name", last_name="Actor2LastName")
        payload = {
            "title": "Play",
            "description": "Description",
            "actors": [actor_1.id, actor_2.id]
        }

        res = self.client.post(PLAY_URL, payload)

        play = Play.objects.get(id=res.data["id"])
        actors = play.actors.all()

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn(actor_1, actors)
        self.assertIn(actor_2, actors)
        self.assertEqual(actors.count(), 2)

    def test_update_play_successful(self):
        play = sample_play(title="Play")

        res = self.client.patch(
            detail_url(play.id),
            {"title": "Updated Title"},
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        play.refresh_from_db()
        self.assertEqual(play.title, "Updated Title")

    def test_delete_play_successful(self):
        play = sample_play(title="Play")

        res = self.client.delete(detail_url(play.id))

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Play.objects.filter(id=play.id).exists())
