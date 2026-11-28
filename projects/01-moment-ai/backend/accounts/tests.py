from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

User = get_user_model()

class AccountApiTests(APITestCase):
    def test_register_creates_user_with_hashed_password(self):
        response = self.client.post("/api/auth/register/", {
            "username": "sri-test", "email": "sri@example.com",
            "first_name": "Sri", "password": "StrongPass!234",
            "password_confirm": "StrongPass!234",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username="sri-test")
        self.assertTrue(user.check_password("StrongPass!234"))

    def test_register_rejects_mismatched_passwords(self):
        response = self.client.post("/api/auth/register/", {
            "username": "another", "email": "another@example.com",
            "password": "StrongPass!234", "password_confirm": "DifferentPass!234",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_and_current_user(self):
        User.objects.create_user(username="login-user", email="login@example.com", password="StrongPass!234")
        token = self.client.post("/api/auth/token/", {
            "username": "login-user", "password": "StrongPass!234"
        }, format="json")
        self.assertEqual(token.status_code, status.HTTP_200_OK)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.data['access']}")
        me = self.client.get("/api/auth/me/")
        self.assertEqual(me.status_code, status.HTTP_200_OK)
        self.assertEqual(me.data["username"], "login-user")
