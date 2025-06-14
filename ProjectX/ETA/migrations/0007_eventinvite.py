# Generated by Django 5.1.6 on 2025-03-24 14:28

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ETA", "0006_attendance"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="EventInvite",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("accepted", "Accepted"),
                            ("pending", "Pending"),
                            ("declined", "Declined"),
                        ],
                        default="pending",
                        max_length=15,
                    ),
                ),
                (
                    "event",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="ETA.event"
                    ),
                ),
                (
                    "from_user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="event_invite_sent",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "to_user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="event_invite_received",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "unique_together": {("event", "from_user", "to_user")},
            },
        ),
    ]
