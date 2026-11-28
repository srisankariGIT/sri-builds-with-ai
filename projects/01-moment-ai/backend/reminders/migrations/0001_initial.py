# Generated for MOMent AI reminders.
import django.conf
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(django.conf.settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name="Reminder",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                ("category", models.CharField(choices=[("Family", "Family"), ("Kids", "Kids"), ("Work", "Work"), ("Health", "Health"), ("Personal", "Personal"), ("Other", "Other")], default="Personal", max_length=50)),
                ("remind_at", models.DateTimeField()),
                ("is_completed", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reminders", to=django.conf.settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("remind_at",)},
        ),
    ]
