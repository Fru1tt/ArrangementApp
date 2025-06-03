# events/management/commands/create_attendances.py

import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from ETA.models import Event, Attendance, Profile

User = get_user_model()

class Command(BaseCommand):
    help = "Populate Attendance entries with realistic numbers and friend clusters."

    def handle(self, *args, **options):
        STATUS_GOING = "going"
        STATUS_CAN_GO = "can_go"
        STATUS_NOT_GOING = "not_going"

        users = list(User.objects.all())
        profiles = {p.user.id: p for p in Profile.objects.select_related("user").all()}

        for event in Event.objects.all():
            title_lower = event.title.lower()
            if "festival" in title_lower:
                target_count = random.randint(300, 600)
            elif any(word in title_lower for word in ["match", "tournament", "competition"]):
                target_count = random.randint(150, 300)
            elif any(word in title_lower for word in ["gokart", "bowling", "paint", "workshop"]):
                target_count = random.randint(50, 120)
            else:
                target_count = random.randint(30, 75)

            base_pool = users.copy()
            random.shuffle(base_pool)
            initial_attendees = base_pool[: min(target_count // 2, len(base_pool)) ]
            attendee_set = set(initial_attendees)

            for user in initial_attendees:
                friend_ids = profiles[user.id].friends.values_list("user__id", flat=True)
                friend_candidates = [u for u in users if u.id in friend_ids and u not in attendee_set]
                friend_sample = random.sample(friend_candidates, k=min(len(friend_candidates), random.randint(5, 15)))
                for friend in friend_sample:
                    attendee_set.add(friend)
                    if len(attendee_set) >= target_count:
                        break
                if len(attendee_set) >= target_count:
                    break

            final_attendees = list(attendee_set)[:target_count]

            for user in final_attendees:
                status = random.choices(
                    [STATUS_GOING, STATUS_CAN_GO, STATUS_NOT_GOING],
                    weights=[0.8, 0.1, 0.1],
                )[0]
                Attendance.objects.get_or_create(user=user, event=event, defaults={"status": status})

        self.stdout.write("Attendance population complete.")