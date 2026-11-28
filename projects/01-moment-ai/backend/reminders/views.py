from rest_framework import generics, filters
from rest_framework.permissions import IsAuthenticated
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
