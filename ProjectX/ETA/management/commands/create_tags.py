# events/management/commands/create_tags.py

from django.core.management.base import BaseCommand
from ETA.models import TagCategory, Tag

class Command(BaseCommand):
    help = "Create predefined TagCategory and Tag entries."

    def handle(self, *args, **options):
        TAG_CATEGORIES = {
            "Music": ["Rock", "Jazz", "Classical", "Pop", "Hip-Hop", "EDM", "Reggae"],
            "Sports": ["Football", "Golf", "Volleyball", "Horse Riding", "Basketball", "Other"],
            "Event Type": ["Festival", "Concert", "Conference", "Exhibition", "Fundraiser", "Lecture", "Meetup", "Networking", "Party", "Seminar", "Webinar", "Workshop"],
            "Food & Drink": ["Bar", "Cooking Class", "Other", "Wine Tasting"],
            "Literature": ["Poetry", "Book Club", "Storytelling"],
            "Venue Type": ["Bar", "Cafe", "Club", "Conference Center", "Gallery", "Lounge", "Marketplace", "Nightclub", "Restaurant", "Stadium", "Theatre"],
            "Price": ["Free", "Paid"],
            "Age": ["18+", "21+", "Any", "Family Friendly"],
            "Setting": ["Indoor", "Outdoor", "Virtual"]
        }

        for category_name, tags in TAG_CATEGORIES.items():
            category_obj, _ = TagCategory.objects.get_or_create(name=category_name)
            for tag_name in tags:
                Tag.objects.get_or_create(name=tag_name, category=category_obj)

        self.stdout.write("TagCategory and Tag entries created.")