from django.contrib import admin
from .models import Reminder

@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "user", "category", "remind_at", "is_completed")
    list_filter = ("category", "is_completed")
    search_fields = ("title", "description", "user__username")
