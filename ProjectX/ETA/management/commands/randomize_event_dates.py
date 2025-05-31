import random
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from ETA.models import Event

class Command(BaseCommand):
    help = 'Randomize all Event start/end dates between July 1 and October 31 of the current year'

    def handle(self, *args, **options):
        tz = timezone.get_current_timezone()
        year = timezone.now().year

        window_start = datetime(year, 7, 1, 0, 0, 0)
        window_end   = datetime(year, 10, 31, 23, 59, 59)

        start_ts = window_start.timestamp()
        end_ts   = window_end.timestamp()

        qs = Event.objects.all()
        total = qs.count()
        for idx, event in enumerate(qs, start=1):
            rand_ts = random.uniform(start_ts, end_ts)
            new_start = timezone.make_aware(datetime.fromtimestamp(rand_ts), tz)
            duration = timedelta(hours=random.randint(1, 5))
            new_end = new_start + duration

            event.start_date = new_start
            event.end_date = new_end
            event.save(update_fields=['start_date', 'end_date'])

            self.stdout.write(f"[{idx}/{total}] {event.title!r} → {new_start}–{new_end}")

        self.stdout.write(self.style.SUCCESS(f"Done! Randomized dates for {total} events."))