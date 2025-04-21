import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from ETA.models import Event, Attendance

User = get_user_model()

class Command(BaseCommand):
    help = "Add extra 'going' attendances to all events except 'Slutsfjell'"

    def handle(self, *args, **options):
        all_users = list(User.objects.all())
        events = Event.objects.exclude(title__iexact="Slutsfjell")

        for ev in events:
            existing = set(
                Attendance.objects
                          .filter(event=ev)
                          .values_list("user_id", flat=True)
            )
            candidates = [u for u in all_users if u.pk not in existing]
            count = min(20, len(candidates))
            for u in random.sample(candidates, k=count):
                Attendance.objects.create(user=u, event=ev, status="going")
            self.stdout.write(f"• {ev.title!r}: added {count} going")
        
        self.stdout.write(self.style.SUCCESS("Done!"))
