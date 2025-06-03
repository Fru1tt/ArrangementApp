# events/management/commands/populate_sample_data.py

import os
import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model
from models import (
    Profile,
    Event,
    TagCategory,
    Tag,
    Attendance,
    FriendRequest,
    EventInvite,
    InviteRequest,
)

User = get_user_model()

class Command(BaseCommand):
    help = "Populate database with a large realistic dataset: users, friend circles, events, attendance, tags, invites, and invite requests."

    def handle(self, *args, **options):
        # CONFIGURATION
        TOTAL_USERS = 200
        PROFILE_IMAGES = [
            "average_inhabitant_.webp",
            "IMG_1456.jpeg",
            "IMG_1987.jpeg",
            "monke.jpg",
            "PP1.jpg",
            "PP4.jpg",
            "pp6.jpg",
            "pp7.jpg",
            "pp8.jpg",
            "pp9.jpg",
            "pp10.jpg",
            "pp11.jpg",
            "pp12.jpg",
            "pp13.jpg",
            "pp14.jpg",
            "pp15.jpg",
            "pp16.jpg",
            "pp18.jpg",
            "pp19.jpg",
            "pp20.jpg",
            "Profile1.png",
            "profile2.png",
        ]
        EVENT_IMAGES = [
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
        TAG_CATEGORIES = {
            "Music": ["Rock", "Jazz", "Classical", "Pop", "Hip-Hop", "EDM"],
            "Sports": ["Football", "Golf", "Volleyball", "Horse Riding", "Basketball"],
            "Festival": ["Summer", "Winter", "Paint", "Food", "Arts", "Cultural"],
            "Game": ["Bowling", "Gokart", "Gel Blaster", "Video Games", "Board Games"],
            "Dinner": ["Tapas", "BBQ", "Fine Dining", "Street Food", "Seafood"],
            "Party": ["Birthday", "Theme", "Sunset", "Tropical", "Chinese"],
            "Literature": ["Poetry", "Book Club", "Storytelling", "Lecture"],
            "Venue Type": ["Bar", "Cafe", "Club", "Conference Center", "Gallery", "Lounge", "Marketplace", "Nightclub", "Restaurant", "Stadium", "Theatre", "Virtual"],
            "Price": ["Free", "Paid"],
            "Age": ["18+", "21+", "Any", "Family Friendly"],
        }
        USER_FIRST_NAMES = [
            "Alex", "Emma", "Liam", "Olivia", "Noah", "Ava", "Elijah", "Isabella",
            "Lucas", "Sophia", "Mia", "Ethan", "Amelia", "James", "Charlotte",
            "Benjamin", "Harper", "Logan", "Evelyn", "Jackson", "Aiden", "Ella",
            "Henry", "Abigail", "Samuel", "Emily", "Daniel", "Avery", "Matthew", "Scarlett",
            "Joseph", "Grace", "David", "Chloe", "Carter", "Victoria", "Owen", "Aria",
            "Wyatt", "Lily", "John", "Zoey", "Jack", "Penelope", "Luke", "Riley",
            "Jayden", "Layla",
        ]
        USER_LAST_NAMES = [
            "Hansen", "Johansen", "Olsen", "Larsen", "Andersen", "Nielsen",
            "Pedersen", "Kristiansen", "Jensen", "Karlsen", "Berg", "Haugen",
            "Lund", "Aas", "Moen", "Heggstad", "Fjeld", "Storm", "Vik", "Solberg",
            "Eriksen", "Johnsen", "Bakken", "Helle", "Nygard", "Strom", "Lie", "Sund",
            "Vester", "Bjornerud",
        ]
        KEYWORD_TO_TAGS = {
            "festival": ("Festival", ["Summer", "Winter", "Paint", "Food", "Arts", "Cultural"]),
            "rock": ("Music", ["Rock"]),
            "gokart": ("Game", ["Gokart"]),
            "bowling": ("Game", ["Bowling"]),
            "golf": ("Sports", ["Golf"]),
            "volleyball": ("Sports", ["Volleyball"]),
            "match": ("Sports", ["Football", "Basketball"]),
            "party": ("Party", ["Birthday", "Theme", "Tropical", "Chinese"]),
            "dinner": ("Dinner", ["Tapas", "BBQ", "Fine Dining", "Seafood"]),
            "lecture": ("Literature", ["Lecture", "Book Club", "Storytelling"]),
            "paint": ("Festival", ["Paint"]),
            "vintage": ("Game", ["Board Games"]),
            "chinese": ("Party", ["Chinese"]),
            "litterær": ("Literature", ["Poetry", "Storytelling"]),
            "vik": ("Venue Type", ["Cafe", "Bar", "Restaurant"]),
            "air_balloons": ("Festival", ["Cultural"]),
            "gel_blaster": ("Game", ["Gel Blaster"]),
            "stadium": ("Sports", ["Football"]),
        }

        # CLEAR existing data (except superuser)
        Attendance.objects.all().delete()
        EventInvite.objects.all().delete()
        InviteRequest.objects.all().delete()
        FriendRequest.objects.all().delete()
        Event.objects.all().delete()
        Tag.objects.all().delete()
        TagCategory.objects.all().delete()
        Profile.objects.all().delete()
        User.objects.exclude(is_superuser=True).delete()

        # CREATE USERS + PROFILES
        users = []
        for i in range(TOTAL_USERS):
            first = random.choice(USER_FIRST_NAMES)
            last = random.choice(USER_LAST_NAMES)
            username = f"{first.lower()}{last.lower()}{i}"
            email = f"{username}@example.com"
            password = "testpassword123"
            user = User.objects.create_user(username=username, email=email, password=password)
            profile = Profile.objects.get(user=user)
            chosen_image = random.choice(PROFILE_IMAGES)
            profile.image.name = f"profile_images/{chosen_image}"
            profile.bio = f"Bio of {first} {last}."
            profile.save()
            users.append(user)

        # FORM FRIEND CIRCLES
        num_circles = TOTAL_USERS // 20  # ~10 users per circle
        circles = []
        all_indices = list(range(TOTAL_USERS))
        random.shuffle(all_indices)
        for c in range(num_circles):
            start_idx = c * 20
            circle_indices = all_indices[start_idx:start_idx + 20]
            circle_users = [users[i] for i in circle_indices]
            for u in circle_users:
                for v in circle_users:
                    if u != v and v not in u.profile.friends.all():
                        u.profile.friends.add(v)
            circles.append(circle_users)
        # CROSS‐CIRCLE ties
        for _ in range(TOTAL_USERS * 2):
            u = random.choice(users)
            v = random.choice(users)
            if u != v and v not in u.profile.friends.all():
                u.profile.friends.add(v)
                v.profile.friends.add(u)

        # BUILD TAGS
        tag_objects = []
        for cat_name, tag_list in TAG_CATEGORIES.items():
            category = TagCategory.objects.create(name=cat_name)
            for tag_name in tag_list:
                t = Tag.objects.create(name=tag_name, category=category)
                tag_objects.append(t)

        # CREATE EVENTS
        events = []
        for filename in EVENT_IMAGES:
            title_raw = os.path.splitext(filename)[0]
            title = title_raw.replace("_", " ").title()
            host = random.choice(users)
            now = timezone.now()
            delta_start = random.randint(-30, 60)
            delta_end_extra = random.randint(1, 7)
            start = now + timedelta(days=delta_start, hours=random.randint(0, 23), minutes=random.randint(0, 59))
            end = start + timedelta(days=delta_end_extra, hours=random.randint(1, 8), minutes=random.randint(0, 59))
            location = random.choice(LOCATIONS)
            is_public = random.choice([True, False])
            description = f"Join us for {title} at {location}. Hosted by {host.username}."
            event = Event.objects.create(
                title=title,
                description=description,
                start_date=start,
                end_date=end,
                is_public=is_public,
                host=host,
                image=f"event_images/{filename}",
                location=location,
            )
            # ASSIGN REALISTIC TAGS
            tags_to_set = set()
            lower_title = title_raw.lower()
            for keyword, (category_name, possible_tags) in KEYWORD_TO_TAGS.items():
                if keyword in lower_title:
                    for pt in possible_tags:
                        tag_obj = Tag.objects.filter(name__iexact=pt, category__name__iexact=category_name).first()
                        if tag_obj:
                            tags_to_set.add(tag_obj)
            if not tags_to_set:
                tags_to_set.update(random.sample(tag_objects, random.randint(1, 2)))
            event.tags.set(list(tags_to_set))
            events.append(event)

        # POPULATE ATTENDANCES
        for event in events:
            title_lower = event.title.lower()
            if "festival" in title_lower:
                count = random.randint(200, 500)
            elif "match" in title_lower or "tournament" in title_lower:
                count = random.randint(150, 300)
            elif "gokart" in title_lower or "bowling" in title_lower:
                count = random.randint(50, 100)
            else:
                count = random.randint(30, 60)
            possible_attendees = users.copy()
            random.shuffle(possible_attendees)
            attendees = possible_attendees[:min(count, len(possible_attendees))]
            for attendee in attendees:
                status = random.choices(
                    ["going", "can_go", "not_going"], weights=[0.6, 0.2, 0.2]
                )[0]
                Attendance.objects.create(user=attendee, event=event, status=status)

        # CREATE EVENT INVITES FOR PRIVATE EVENTS
        private_events = [e for e in events if not e.is_public]
        for event in private_events:
            inviter = event.host
            invite_count = random.randint(50, 100)
            possible_invitees = [u for u in users if u != inviter]
            random.shuffle(possible_invitees)
            invitees = possible_invitees[:invite_count]
            for invitee in invitees:
                status = random.choices(["accepted", "pending", "declined"], weights=[0.5, 0.3, 0.2])[0]
                EventInvite.objects.create(
                    event=event,
                    from_user=inviter,
                    to_user=invitee,
                    status=status,
                )

        # CREATE INVITE REQUESTS BETWEEN RANDOM USERS
        for _ in range(100):
            event = random.choice(events)
            requester = random.choice(users)
            requested_user = random.choice([u for u in users if u != requester])
            try:
                InviteRequest.objects.create(
                    event=event,
                    requested_by=requester,
                    requested_user=requested_user,
                )
            except:
                continue

        # CREATE FRIEND REQUESTS AMONG NON‐FRIENDS
        for _ in range(100):
            frm = random.choice(users)
            to = random.choice([u for u in users if u != frm and u not in frm.profile.friends.all()])
            try:
                FriendRequest.objects.create(from_user=frm, to_user=to)
            except:
                continue

        self.stdout.write("Large-scale sample data population complete.")