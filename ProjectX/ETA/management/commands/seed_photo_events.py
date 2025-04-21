import os
import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings
from ETA.models import Event, Attendance

User = get_user_model()

from ETA.models import Profile

PHOTO_EVENTS = [
    {
        "photo": "GPT1.png",
        "title": "Summer Music Festival",
        "desc": "Join us for a night of live bands under the stars at the annual Summer Music Festival.",
        "days_offset": 7,
        "hours": (18, 23),
    },
    {
        "photo": "gpt2.jpg",
        "title": "Sunset Beach Gala",
        "desc": "A beachfront gala with dinner, cocktails, and dancing at golden hour.",
        "days_offset": 10,
        "hours": (17, 21),
    },
    {
        "photo": "gpt3.jpg",
        "title": "Color Run Carnival",
        "desc": "A fun run through clouds of color followed by carnival games and food trucks.",
        "days_offset": 14,
        "hours": (9, 13),
    },
    {
        "photo": "gpt1.png",
        "title": "Open-Air Concert",
        "desc": "Catch your favorite local acts performing live in the historic town square.",
        "days_offset": 5,
        "hours": (16, 20),
    },
    {
        "photo": "gpt4.jpg",
        "title": "Stadium Pop-Up Show",
        "desc": "Exclusive pop-up performance at the old stadium—limited tickets!",
        "days_offset": 12,
        "hours": (19, 22),
    },
    {
        "photo": "gpt5.webp",
        "title": "Gourmet Buffet Affair",
        "desc": "An exquisite spread of international cuisines in a chic urban loft.",
        "days_offset": 9,
        "hours": (18, 22),
    },
    {
        "photo": "gpt6.png",
        "title": "Neon Gel Blaster Battle",
        "desc": "High‑energy, glow‑in‑the‑dark gel‑blaster arena competition.",
        "days_offset": 3,
        "hours": (14, 18),
    },
    {
        "photo": "gpt7.jpg",
        "title": "Sunset Volleyball Meetup",
        "desc": "Friendly beach volleyball games at dusk—bring your own team or join one!",
        "days_offset": 8,
        "hours": (17, 20),
    },
    {
        "photo": "gpt8.jpg",
        "title": "Main Event Bowling Night",
        "desc": "Strike! Family and friends bowling night at Main Event bowling alley.",
        "days_offset": 11,
        "hours": (18, 21),
    },
    {
        "photo": "gpt10.jpeg",
        "title": "Lantern Festival Gala",
        "desc": "An evening of floating lanterns and live performances in the palace courtyard.",
        "days_offset": 15,
        "hours": (19, 23),
    },
]

class Command(BaseCommand):
    help = "Seed 10 new events based on photos + realistic attendance"

    def handle(self, *args, **options):
        self.stdout.write("Seeding photo‐based events…")

        all_users = list(User.objects.all())
        if len(all_users) < 10:
            self.stderr.write("Need at least 10 users in the system!")
            return

        # maybe expand carlgrude1's friendships here:
        try:
            carl = User.objects.get(username='carlgrude1')
            p = carl.profile
            # ensure at least 23 friends
            others = [u for u in all_users if u != carl]
            needed = 23 - p.friends.count()
            if needed > 0:
                picks = random.sample(others, k=min(needed, len(others)))
                for u in picks:
                    p.friends.add(u.profile)
                p.save()
                self.stdout.write(f" — extended carlgrude1 to {p.friends.count()} friends")
        except User.DoesNotExist:
            self.stdout.write(" — carlgrude1 not found, skipping friendship boost")

        # Helper to build datetime
        def mk_dt(offset_days, start_hour, end_hour):
            now = datetime.now()
            start = now + timedelta(days=offset_days, hours=start_hour - now.hour)
            end   = start + timedelta(hours=(end_hour - start_hour))
            return start, end

        for i, ev_data in enumerate(PHOTO_EVENTS, start=1):
            title = ev_data['title']
            start_dt, end_dt = mk_dt(ev_data['days_offset'], *ev_data['hours'])
            image = os.path.join(settings.MEDIA_ROOT, 'event_images', ev_data['photo'])

            # create the event
            ev, created = Event.objects.get_or_create(
                title=title,
                defaults={
                    'description': ev_data['desc'],
                    'start_date': start_dt,
                    'end_date':   end_dt,
                    'is_public':  True,
                    'host':       random.choice(all_users),
                    'image':      f"event_images/{ev_data['photo']}"
                }
            )
            if created:
                self.stdout.write(f" • Created event #{ev.pk}: {title}")
            else:
                self.stdout.write(f" • Skipped existing event #{ev.pk}: {title}")

            # choose a “friend group” around one random user
            host = ev.host
            # grab the Profile objects, then pull their .user
            friend_profiles = list(host.profile.friends.all())
            friend_users    = [p.user for p in friend_profiles]
            random.shuffle(friend_users)
            fg = friend_users[: random.randint(5, 15)]

            # attendance buckets
            bucket_going    = fg
            bucket_interested = random.sample(all_users, k=random.randint(3,10))
            bucket_notgoing = random.sample(all_users, k=random.randint(3,10))

            # ensure no overlap
            bucket_interested = [u for u in bucket_interested if u not in bucket_going]
            bucket_notgoing   = [u for u in bucket_notgoing   if u not in bucket_going + bucket_interested]

            # seed them
            for u in bucket_going:
                Attendance.objects.update_or_create(
                    user=u, event=ev,
                    defaults={'status':'going'}
                )
            for u in bucket_interested:
                Attendance.objects.update_or_create(
                    user=u, event=ev,
                    defaults={'status':'can go'}
                )
            for u in bucket_notgoing:
                Attendance.objects.update_or_create(
                    user=u, event=ev,
                    defaults={'status':'not going'}
                )

            self.stdout.write(
                f"   ↳ Going: {len(bucket_going)}, "
                f"Can Go: {len(bucket_interested)}, "
                f"Not Going: {len(bucket_notgoing)}"
            )

        self.stdout.write(self.style.SUCCESS("Done seeding 10 photo events!"))
