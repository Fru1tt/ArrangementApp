# events/management/commands/create_tags.py

from django.core.management.base import BaseCommand
from ETA.models import TagCategory, Tag

class Command(BaseCommand):
    help = "Create predefined TagCategory and Tag entries."

    def handle(self, *args, **options):
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

        for category_name, tags in TAG_CATEGORIES.items():
            category_obj, _ = TagCategory.objects.get_or_create(name=category_name)
            for tag_name in tags:
                Tag.objects.get_or_create(name=tag_name, category=category_obj)

        self.stdout.write("TagCategory and Tag entries created.")