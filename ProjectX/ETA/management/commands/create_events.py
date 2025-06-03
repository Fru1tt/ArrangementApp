# events/management/commands/create_events.py

import os
import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from ETA.models import Event

User = get_user_model()

class Command(BaseCommand):
    help = "Create public Event entries with realistic title, description, location, dates, and image. 'jan' hosts two events."

    def handle(self, *args, **options):
        JAN_USER = User.objects.filter(username="jan").first()
        IMAGE_FILENAMES = [
            "bislet_festival.jpg",
            "Bowling_party.jpg",
            "brunsj.jpg",
            "bursdag.webp",
            "chinese_theme_party.jpeg",
            "Gaia.png",
            "gel_blaster_competition.png",
            "gokart.jpg",
            "golf_tournament.jpeg",
            "guttas_aften.jpeg",
            "hagefest.webp",
            "Hot_air_balloons.webp",
            "Litterær_Lørdag.jpg",
            "liverpool_match.jpeg",
            "monke.jpg",
            "paint_festival.jpg",
            "påskegames.jpeg",
            "Slottsfjell.jpg",
            "Sommerrock.jpg",
            "stavern_festival.png",
            "summer_dinner.jpg",
            "sunset_volleyball.jpg",
            "tapas_evening.webp",
            "totalpeople_icon.png",
            "Tropisk_torsdag.jpg",
            "Vayr_festival.jpg",
            "Vintage_spillkveld.jpg",
            "Vintermarked_rørs.webp",
        ]
        LOCATIONS = [
            "Central Park, New York, NY",
            "Oslo Opera House, Oslo, Norway",
            "Slottsfjell Amfi, Tønsberg, Norway",
            "Gardermoen Airport, Oslo, Norway",
            "Stavern, Norway",
            "Munich Football Arena, Munich, Germany",
            "Hyde Park, London, UK",
            "Ekebergparken, Oslo, Norway",
            "Vigeland Sculpture Park, Oslo, Norway",
            "Majorstuen Metro Station, Oslo, Norway",
            "Lillehammer Olympic Park, Lillehammer, Norway",
            "Aker Brygge, Oslo, Norway",
            "Trondheim Sentrum, Trondheim, Norway",
            "Bergen Fish Market, Bergen, Norway",
            "Camden Town, London, UK",
            "Coney Island, Brooklyn, NY",
            "Santa Monica Pier, Santa Monica, CA",
            "Golden Gate Park, San Francisco, CA",
            "Bondi Beach, Sydney, Australia",
            "Copacabana, Rio de Janeiro, Brazil",
        ]
        all_users = list(User.objects.all())
        now = timezone.now()
        created = 0

        # Two events hosted by jan
        jan_images = random.sample(IMAGE_FILENAMES, 2)
        for filename in jan_images:
            title_raw = os.path.splitext(filename)[0]
            title = title_raw.replace("_", " ").title()
            delta_days = random.randint(1, 60)
            delta_hours = random.randint(8, 20)
            start = now + timedelta(days=delta_days, hours=delta_hours)
            duration = timedelta(hours=random.randint(2, 8))
            end = start + duration
            location = random.choice(LOCATIONS)
            description = (
                f"{title} will take place on {start.strftime('%B %d, %Y at %H:%M')} "
                f"at {location}. Hosted by jan."
            )
            Event.objects.create(
                title=title,
                description=description,
                start_date=start,
                end_date=end,
                is_public=True,
                host=JAN_USER,
                image=f"event_images/{filename}",
                location=location,
            )
            created += 1
            IMAGE_FILENAMES.remove(filename)

        # Remaining events with random hosts
        for filename in IMAGE_FILENAMES:
            title_raw = os.path.splitext(filename)[0]
            title = title_raw.replace("_", " ").title()
            host = random.choice(all_users)
            delta_days = random.randint(1, 60)
            delta_hours = random.randint(8, 20)
            start = now + timedelta(days=delta_days, hours=delta_hours)
            duration = timedelta(hours=random.randint(2, 8))
            end = start + duration
            location = random.choice(LOCATIONS)
            description = (
                f"{title} will take place on {start.strftime('%B %d, %Y at %H:%M')} "
                f"at {location}. Hosted by {host.username}."
            )
            Event.objects.create(
                title=title,
                description=description,
                start_date=start,
                end_date=end,
                is_public=True,
                host=host,
                image=f"event_images/{filename}",
                location=location,
            )
            created += 1

        self.stdout.write(f"Created {created} public events.")