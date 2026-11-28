import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import filters, generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Reminder
from .serializers import ReminderSerializer


class ReminderListCreateView(generics.ListCreateAPIView):
    serializer_class = ReminderSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "description", "category"]
    ordering_fields = ["remind_at", "created_at", "title"]

    def get_queryset(self):
        queryset = Reminder.objects.filter(user=self.request.user)
        category = self.request.query_params.get("category")
        completed = self.request.query_params.get("is_completed")
        if category:
            queryset = queryset.filter(category__iexact=category)
        if completed in ("true", "false"):
            queryset = queryset.filter(is_completed=(completed == "true"))
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ReminderDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ReminderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Reminder.objects.filter(user=self.request.user)


class ParseReminderView(APIView):
    """Turn a natural-language request into a draft; never save it automatically."""
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "ai_parse"

    def post(self, request):
        text = request.data.get("text", "")
        if not isinstance(text, str) or not text.strip():
            return Response({"error": "Enter what you want to remember."}, status=status.HTTP_400_BAD_REQUEST)
        if len(text) > 1000:
            return Response({"error": "Please keep the request under 1,000 characters."}, status=status.HTTP_400_BAD_REQUEST)

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return Response(
                {"error": "AI drafting is not configured yet. You can still create a reminder using the form."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        now = timezone.localtime().isoformat()
        payload = {
            "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Extract a family reminder from the user's text. Current local date and time is "
                        f"{now} in Asia/Kolkata. Return JSON only with keys: title, description, category, "
                        "remind_at, needs_clarification, clarification_question. category must be one of "
                        "Family, Kids, Work, Health, Personal, Other. remind_at must be an ISO 8601 datetime "
                        "with timezone offset, or null. If the user has not provided enough information to "
                        "identify a reminder time, set needs_clarification=true and ask one short question. "
                        "Do not invent a date or time. If the date/time is ambiguous, ask for clarification. "
                        "If the reminder time is in the past, ask for a future date/time. Never claim the "
                        "reminder has been saved."
                    ),
                },
                {"role": "user", "content": text.strip()},
            ],
        }
        outbound = Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(outbound, timeout=20) as response:
                result = json.loads(response.read().decode("utf-8"))
            content = result["choices"][0]["message"]["content"]
            draft = json.loads(content)
        except (HTTPError, URLError, TimeoutError, KeyError, IndexError, ValueError, json.JSONDecodeError):
            return Response(
                {"error": "I couldn't prepare that reminder right now. Please try again or use the form."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        title = str(draft.get("title") or "").strip()
        category = draft.get("category") or "Personal"
        remind_at_raw = draft.get("remind_at")
        remind_at = parse_datetime(remind_at_raw) if isinstance(remind_at_raw, str) else None
        if remind_at and timezone.is_naive(remind_at):
            remind_at = timezone.make_aware(remind_at, timezone.get_current_timezone())

        if draft.get("needs_clarification") or not title or not remind_at:
            return Response({
                "needs_clarification": True,
                "question": draft.get("clarification_question") or "What date and time should I remind you?",
            })

        if remind_at <= timezone.now():
            return Response({
                "needs_clarification": True,
                "question": "That time has already passed. What future date and time should I use?",
            })

        allowed_categories = {choice[0] for choice in Reminder.CATEGORIES}
        if category not in allowed_categories:
            category = "Personal"

        return Response({
            "needs_clarification": False,
            "draft": {
                "title": title[:255],
                "description": str(draft.get("description") or "")[:2000],
                "category": category,
                "remind_at": remind_at.isoformat(),
            },
            "requires_confirmation": True,
        })
