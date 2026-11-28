from datetime import timedelta
import json
import os
from unittest.mock import MagicMock, patch
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Reminder

User = get_user_model()

class ReminderApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="owner", password="StrongPass!234")
        self.other = User.objects.create_user(username="other", password="StrongPass!234")
        self.client.force_authenticate(self.user)
        self.payload = {
            "title": "School pickup", "description": "Pick up at the main gate",
            "category": "Kids", "remind_at": (timezone.now() + timedelta(days=1)).isoformat(),
        }

    def test_create_and_list_reminder(self):
        created = self.client.post("/api/reminders/", self.payload, format="json")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        self.assertEqual(created.data["title"], "School pickup")
        self.assertEqual(self.client.get("/api/reminders/").data[0]["title"], "School pickup")

    def test_user_only_sees_own_reminders(self):
        Reminder.objects.create(user=self.other, title="Private", category="Personal", remind_at=timezone.now() + timedelta(days=1))
        response = self.client.get("/api/reminders/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_user_cannot_retrieve_another_users_reminder(self):
        private = Reminder.objects.create(user=self.other, title="Private", category="Personal", remind_at=timezone.now() + timedelta(days=1))
        self.assertEqual(self.client.get(f"/api/reminders/{private.id}/").status_code, status.HTTP_404_NOT_FOUND)

    def test_update_and_delete_own_reminder(self):
        item = Reminder.objects.create(user=self.user, title="Old", category="Personal", remind_at=timezone.now() + timedelta(days=1))
        update = self.client.patch(f"/api/reminders/{item.id}/", {"title": "Updated"}, format="json")
        self.assertEqual(update.status_code, status.HTTP_200_OK)
        self.assertEqual(update.data["title"], "Updated")
        self.assertEqual(self.client.delete(f"/api/reminders/{item.id}/").status_code, status.HTTP_204_NO_CONTENT)

    def test_rejects_past_date(self):
        payload = {**self.payload, "remind_at": (timezone.now() - timedelta(days=1)).isoformat()}
        self.assertEqual(self.client.post("/api/reminders/", payload, format="json").status_code, status.HTTP_400_BAD_REQUEST)

    def test_requires_authentication(self):
        self.client.force_authenticate(user=None)
        self.assertIn(self.client.get("/api/reminders/").status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_ai_parse_requires_configuration_and_does_not_save(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
            response = self.client.post("/api/reminders/parse/", {"text": "Remind me tomorrow"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(Reminder.objects.count(), 0)

    def test_ai_parse_requires_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.post("/api/reminders/parse/", {"text": "Remind me tomorrow at 9 AM"}, format="json")
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    @patch("reminders.views.urlopen")
    def test_ai_parse_returns_reviewable_draft_without_saving(self, mocked_urlopen):
        mocked_response = MagicMock()
        mocked_response.__enter__.return_value.read.return_value = json.dumps({
            "choices": [{"message": {"content": json.dumps({
                "title": "School pickup",
                "description": "Pick up from the main gate",
                "category": "Kids",
                "remind_at": (timezone.now() + timedelta(days=1)).isoformat(),
                "needs_clarification": False,
                "clarification_question": "",
            })}}],
        }).encode("utf-8")
        mocked_urlopen.return_value = mocked_response
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            response = self.client.post("/api/reminders/parse/", {"text": "Pick up kids tomorrow at 3 PM"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["requires_confirmation"])
        self.assertEqual(response.data["draft"]["title"], "School pickup")
        self.assertEqual(Reminder.objects.count(), 0)

    @patch("reminders.views.urlopen")
    def test_ai_parse_asks_for_missing_time(self, mocked_urlopen):
        mocked_response = MagicMock()
        mocked_response.__enter__.return_value.read.return_value = json.dumps({
            "choices": [{"message": {"content": json.dumps({
                "title": "Buy groceries",
                "description": "",
                "category": "Family",
                "remind_at": None,
                "needs_clarification": True,
                "clarification_question": "What time should I remind you?",
            })}}],
        }).encode("utf-8")
        mocked_urlopen.return_value = mocked_response
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            response = self.client.post("/api/reminders/parse/", {"text": "Buy groceries"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["needs_clarification"])
        self.assertIn("time", response.data["question"])
        self.assertEqual(Reminder.objects.count(), 0)
