from django.utils import timezone
from rest_framework import serializers
from .models import Reminder

class ReminderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reminder
        fields = ("id", "title", "description", "category", "remind_at", "is_completed", "created_at")
        read_only_fields = ("id", "created_at")

    def validate_title(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Please enter a reminder title.")
        return value

    def validate_remind_at(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError("Choose a date and time in the future.")
        return value
