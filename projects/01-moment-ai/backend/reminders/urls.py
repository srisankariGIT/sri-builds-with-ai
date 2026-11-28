from django.urls import path
from .views import ParseReminderView, ReminderDetailView, ReminderListCreateView

urlpatterns = [
    path("", ReminderListCreateView.as_view(), name="reminder-list-create"),
    path("parse/", ParseReminderView.as_view(), name="reminder-parse"),
    path("<int:pk>/", ReminderDetailView.as_view(), name="reminder-detail"),
]
