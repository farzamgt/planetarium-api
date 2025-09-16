from random import randint
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from planetarium.models import PlanetariumDome, ShowTheme, AstronomyShow, ShowSession
from planetarium.serializers import (
    PlanetariumDomeSerializer, ShowThemeSerializer,
    AstronomyShowSerializer, ShowSessionListSerializer
)


def sample_dome(name="Dome 1"):
    return PlanetariumDome.objects.create(name=name, rows=5, seats_in_row=10)


def sample_theme(name="Space"):
    return ShowTheme.objects.create(name=f"{name}_{randint(1,10000)}")


def sample_show(title="Sample Show"):
    theme = sample_theme()
    return AstronomyShow.objects.create(title=title, description="Sample description", theme=theme)


def sample_session():
    show = sample_show()
    dome = sample_dome()
    from datetime import datetime, timedelta
    show_time = datetime.now() + timedelta(days=1)
    return ShowSession.objects.create(show_time=show_time, astronomy_show=show, planetarium_dome=dome)


class PlanetariumViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="user@example.com", password="testpass"
        )
        self.admin = get_user_model().objects.create_superuser(
            email="admin@example.com", password="adminpass"
        )
        self.client.force_authenticate(user=self.user)

    def test_list_domes(self):
        dome = sample_dome()
        url = reverse("planetarium:planetariumdome-list")
        res = self.client.get(url)
        domes = PlanetariumDome.objects.all()
        serializer = PlanetariumDomeSerializer(domes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.data.get("results", [])  # <-- дістаємо "results"
        self.assertEqual(data, serializer.data)

    def test_create_dome_forbidden_for_user(self):
        url = reverse("planetarium:planetariumdome-list")
        payload = {"name": "New Dome", "rows": 5, "seats_in_row": 10, "capacity": 50}
        res = self.client.post(url, payload, format="json")
        self.assertIn(res.status_code, (status.HTTP_403_FORBIDDEN, status.HTTP_405_METHOD_NOT_ALLOWED))

    def test_create_dome_as_admin(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse("planetarium:planetariumdome-list")
        payload = {"name": "Admin Dome", "rows": 5, "seats_in_row": 10, "capacity": 50}
        res = self.client.post(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(PlanetariumDome.objects.filter(name="Admin Dome").exists())

    def test_list_shows_with_filter(self):
        show1 = sample_show(title="Show 1")
        show2 = sample_show(title="Show 2")
        url = reverse("planetarium:astronomyshow-list") + "?title=Show 1"
        res = self.client.get(url)
        serializer = AstronomyShowSerializer([show1], many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.data.get("results", [])
        self.assertEqual(data, serializer.data)

    def test_list_sessions(self):
        session = sample_session()
        url = reverse("planetarium:showsession-list")
        res = self.client.get(url)

        from django.db.models import F, Count
        sessions = ShowSession.objects.annotate(
            tickets_available=F("planetarium_dome__rows") * F("planetarium_dome__seats_in_row") - Count("tickets")
        )

        serializer = ShowSessionListSerializer(
            sessions, many=True, context={"request": res.wsgi_request}
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.data.get("results", [])
        self.assertEqual(len(data), len(serializer.data))
        for d, s in zip(data, serializer.data):
            self.assertEqual(d["id"], s["id"])
            self.assertEqual(d["show_time"], s["show_time"])
            self.assertEqual(d["tickets_available"], s["tickets_available"])


class ShowThemeViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="user@example.com", password="testpass"
        )
        self.admin = get_user_model().objects.create_superuser(
            email="admin@example.com", password="adminpass"
        )
        self.client.force_authenticate(user=self.user)

    def test_list_themes(self):
        theme = sample_theme()
        url = reverse("planetarium:showtheme-list")
        res = self.client.get(url)
        serializer = ShowThemeSerializer(ShowTheme.objects.all(), many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.data.get("results", [])
        self.assertEqual(data, serializer.data)

    def test_create_theme_forbidden_for_user(self):
        url = reverse("planetarium:showtheme-list")
        payload = {"name": "New Theme"}
        res = self.client.post(url, payload, format="json")
        self.assertIn(res.status_code, (status.HTTP_403_FORBIDDEN, status.HTTP_405_METHOD_NOT_ALLOWED))

    def test_create_theme_as_admin(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse("planetarium:showtheme-list")
        payload = {"name": "Admin Theme"}
        res = self.client.post(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(ShowTheme.objects.filter(name="Admin Theme").exists())


class AstronomyShowViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="user@example.com", password="testpass"
        )
        self.admin = get_user_model().objects.create_superuser(
            email="admin@example.com", password="adminpass"
        )
        self.client.force_authenticate(user=self.user)

    def test_list_shows_filtered_by_title(self):
        show1 = sample_show(title="Show 1")
        show2 = sample_show(title="Show 2")
        url = reverse("planetarium:astronomyshow-list") + "?title=Show 1"
        res = self.client.get(url)
        serializer = AstronomyShowSerializer([show1], many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.data.get("results", [])
        self.assertEqual(data, serializer.data)

    def test_list_shows_filtered_by_theme(self):
        theme1 = sample_theme("Theme1")
        theme2 = sample_theme("Theme2")
        show1 = AstronomyShow.objects.create(title="Show 1", description="Desc", theme=theme1)
        show2 = AstronomyShow.objects.create(title="Show 2", description="Desc", theme=theme2)
        url = reverse("planetarium:astronomyshow-list") + f"?theme={theme1.id}"
        res = self.client.get(url)
        serializer = AstronomyShowSerializer([show1], many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.data.get("results", [])
        self.assertEqual(data, serializer.data)

    def test_create_show_forbidden_for_user(self):
        url = reverse("planetarium:astronomyshow-list")
        payload = {"title": "New Show", "description": "Desc", "theme": sample_theme().id}
        res = self.client.post(url, payload, format="json")
        self.assertIn(res.status_code, (status.HTTP_403_FORBIDDEN, status.HTTP_405_METHOD_NOT_ALLOWED))

    def test_create_show_as_admin(self):
        self.client.force_authenticate(user=self.admin)
        theme = sample_theme()
        url = reverse("planetarium:astronomyshow-list")
        payload = {"title": "Admin Show", "description": "Desc", "theme": theme.id}
        res = self.client.post(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(AstronomyShow.objects.filter(title="Admin Show").exists())

    def test_retrieve_show(self):
        show = sample_show()
        url = reverse("planetarium:astronomyshow-detail", args=[show.id])
        res = self.client.get(url)
        serializer = AstronomyShowSerializer(show)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
