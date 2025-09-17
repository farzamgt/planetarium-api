from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

REGISTER_URL = "/api/user/register/"
LOGIN_URL = "/api/user/login/"
ME_URL = "/api/user/me/"


class UserApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_model = get_user_model()

    def test_create_user_success(self):
        payload = {"email": "test@example.com", "password": "testpass123"}
        res = self.client.post(REGISTER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = self.user_model.objects.get(email=payload["email"])
        self.assertTrue(user.check_password(payload["password"]))

    def test_create_user_invalid_email(self):
        payload = {"email": "", "password": "testpass123"}
        res = self.client.post(REGISTER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_user_success(self):
        self.user_model.objects.create_user(
            email="test@example.com", password="testpass123"
        )
        payload = {"email": "test@example.com", "password": "testpass123"}
        res = self.client.post(LOGIN_URL, payload)
        self.assertIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_login_user_fail(self):
        self.user_model.objects.create_user(
            email="test@example.com", password="testpass123"
        )
        payload = {"email": "test@example.com", "password": "wrongpass"}
        res = self.client.post(LOGIN_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized(self):
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_user_authorized(self):
        user = self.user_model.objects.create_user(
            email="test@example.com", password="testpass123"
        )
        res_login = self.client.post(
            LOGIN_URL,
            {"email": user.email, "password": "testpass123"}
        )
        token = res_login.data["token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["email"], user.email)
