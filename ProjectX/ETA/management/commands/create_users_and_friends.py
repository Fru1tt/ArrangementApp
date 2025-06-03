# events/management/commands/create_users_and_friends.py

import random
import math
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth import get_user_model
from ETA.models import Profile

# Use a fast hasher for bulk user creation
settings.PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

User = get_user_model()

class Command(BaseCommand):
    help = "Generate 500 users and assign realistic friend relationships, including existing users 'jan' and 'FK'."

    def handle(self, *args, **options):
        TOTAL_NEW_USERS = 500

        FIRST_NAMES = [
            "Alex", "Emma", "Liam", "Olivia", "Noah", "Ava", "Elijah", "Isabella",
            "Lucas", "Sophia", "Mia", "Ethan", "Amelia", "James", "Charlotte",
            "Benjamin", "Harper", "Logan", "Evelyn", "Jackson", "Aiden", "Ella",
            "Henry", "Abigail", "Samuel", "Emily", "Daniel", "Avery", "Matthew", "Scarlett",
            "Joseph", "Grace", "David", "Chloe", "Carter", "Victoria", "Owen", "Aria",
            "Wyatt", "Lily", "John", "Zoey", "Jack", "Penelope", "Luke", "Riley",
            "Jayden", "Layla",
        ]

        LAST_NAMES = [
            "Hansen", "Johansen", "Olsen", "Larsen", "Andersen", "Nielsen",
            "Pedersen", "Kristiansen", "Jensen", "Karlsen", "Berg", "Haugen",
            "Lund", "Aas", "Moen", "Heggstad", "Fjeld", "Storm", "Vik", "Solberg",
            "Eriksen", "Johnsen", "Bakken", "Helle", "Nygard", "Strom", "Lie", "Sund",
            "Vester", "Bjornerud",
        ]

        created_users = []

        # Ensure premade users 'jan' and 'FK' exist
        for username in ["jan", "FK"]:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"email": f"{username}@example.com"}
            )
            if created:
                user.set_password("password123")
                user.save()
            # Ensure profile exists
            profile, _ = Profile.objects.get_or_create(user=user)
            created_users.append(user)

        # Create 500 new users
        for i in range(TOTAL_NEW_USERS):
            first = random.choice(FIRST_NAMES)
            last = random.choice(LAST_NAMES)
            username = f"{first.lower()}{last.lower()}{i}"
            email = f"{username}@example.com"
            password = "password123"
            user = User.objects.create_user(username=username, email=email, password=password)
            # Access profile to trigger creation via signal
            profile, _ = Profile.objects.get_or_create(user=user)
            created_users.append(user)

        total_users = len(created_users)

        # Form friend circles of size ~25
        circle_size = 25
        num_circles = math.ceil(total_users / circle_size)
        indices = list(range(total_users))
        random.shuffle(indices)

        circles = []
        for c in range(num_circles):
            start = c * circle_size
            end = start + circle_size
            circle_indices = indices[start:end]
            circle_users = [created_users[i] for i in circle_indices if i < total_users]
            circles.append(circle_users)

        # Within each circle, connect every user pair via their profiles
        for circle in circles:
            for i in range(len(circle)):
                u = circle[i]
                u_profile = u.profile
                for j in range(i + 1, len(circle)):
                    v = circle[j]
                    v_profile = v.profile
                    if v_profile not in u_profile.friends.all():
                        u_profile.friends.add(v_profile)
                        v_profile.friends.add(u_profile)

        # Add cross-circle friendships to simulate realistic network
        extra_ties = total_users * 2
        for _ in range(extra_ties):
            u = random.choice(created_users)
            v = random.choice(created_users)
            if u != v:
                u_profile = u.profile
                v_profile = v.profile
                if v_profile not in u_profile.friends.all():
                    u_profile.friends.add(v_profile)
                    v_profile.friends.add(u_profile)

        self.stdout.write(f"Created {TOTAL_NEW_USERS} new users (plus 'jan' and 'FK') and assigned friend relationships.")