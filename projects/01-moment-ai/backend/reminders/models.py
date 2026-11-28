from django.conf import settings
from django.db import models

class Reminder(models.Model):
    CATEGORIES = [
        ("Family", "Family"), ("Kids", "Kids"), ("Work", "Work"),
        ("Health", "Health"), ("Personal", "Personal"), ("Other", "Other"),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reminders")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, choices=CATEGORIES, default="Personal")
    remind_at = models.DateTimeField()
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("remind_at",)

    def __str__(self):
        return self.title
