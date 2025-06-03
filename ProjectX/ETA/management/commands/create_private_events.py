# events/management/commands/create_private_events.py

import os
import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from ETA.models import Event, Attendance, Profile

User = get_user_model()

class Command(BaseCommand):
    help = "Create private events where Jan is invited, not hosting, with 5–15 attendees including Jan and some of his friends."

    def handle(self, *args, **options):
        JAN = User.objects.filter(username="jan").first()
        if not JAN:
            self.stdout.write("User 'jan' not found.")
            return

        JAN_FRIEND_IDS = list(Profile.objects.get(user=JAN).friends.values_list("user__id", flat=True))
        OTHER_USERS = list(User.objects.exclude(username="jan"))
        NOW = timezone.now()

        LOCATIONS = [
            "Aker Brygge, Oslo, Norway",
            "Tøyen Park, Oslo, Norway",
            "Sagene, Oslo, Norway",
            "Majorstuen Metro Station, Oslo, Norway",
            "Ekeberg, Oslo, Norway",
            "Grønland, Oslo, Norway",
            "St. Hanshaugen, Oslo, Norway",
            "Vigeland Sculpture Park, Oslo, Norway",
        ]

        IMAGES = [
            "ExamAfter-party.png",
            "FamilyGathering.jpg",
            "grass_watching.jpg",
            "karaoke.png",
            "treehugging.jpg",
        ]

        for filename in IMAGES:
            title_raw = os.path.splitext(filename)[0]
            title = title_raw.replace("-", " ").replace("_", " ").title()

            host = random.choice(OTHER_USERS)

            days_ahead = random.randint(1, 30)
            hour = random.randint(18, 23)
            start = NOW + timedelta(days=days_ahead, hours=hour)
            end = start + timedelta(hours=random.randint(2, 4))

            location = random.choice(LOCATIONS)
            description = (
                f"{title} on {start.strftime('%B %d, %Y at %H:%M')} "
                f"at {location}. Hosted by {host.username}."
            )

            event = Event.objects.create(
                title=title,
                description=description,
                start_date=start,
                end_date=end,
                is_public=False,
                host=host,
                image=f"event_images/{filename}",
                location=location,
            )

            attendees = set()

            Attendance.objects.create(user=JAN, event=event, status="going")
            attendees.add(JAN.id)

            num_friends = min(len(JAN_FRIEND_IDS), random.randint(2, 5))
            selected_friend_ids = random.sample(JAN_FRIEND_IDS, num_friends) if JAN_FRIEND_IDS else []
            for uid in selected_friend_ids:
                user = User.objects.get(id=uid)
                Attendance.objects.create(user=user, event=event, status="going")
                attendees.add(uid)

            total_attendees = random.randint(5, 15)
            remaining = total_attendees - len(attendees)

            pool = [u for u in OTHER_USERS if u.id not in attendees]
            random.shuffle(pool)
            for user in pool[:remaining]:
                Attendance.objects.create(user=user, event=event, status="going")

        self.stdout.write(f"Created {len(IMAGES)} private events with Jan invited to each.")