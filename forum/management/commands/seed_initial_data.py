from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from forum.models import Category, Section, Venue

CATEGORIES = [
    {
        "name": "Lines and Crowds",
        "description": "Queue updates, entry congestion, gate delays.",
        "order": 1,
    },
    {
        "name": "Food and Drinks",
        "description": "Concessions updates, availability reports, recommendations.",
        "order": 2,
    },
    {
        "name": "Fan Vibe",
        "description": "Atmosphere updates, crowd energy, celebration moments.",
        "order": 3,
    },
    {
        "name": "Help",
        "description": "Lost items, direction requests, non-emergency assistance.",
        "disclaimer": (
            "For medical or security emergencies, please contact stadium staff directly."
        ),
        "order": 4,
    },
]

GROUPS = ["Venue Admin", "Moderator"]

VENUES = [
    {
        "name": "Riverside Stadium",
        "location": "1 Riverside Way",
        "sections": ["North Stand", "South Stand", "VIP"],
    },
]


class Command(BaseCommand):
    help = "Seed initial reference data: post categories, base groups, and a sample venue."

    def handle(self, *args, **options):
        for data in CATEGORIES:
            category, created = Category.objects.update_or_create(
                name=data["name"], defaults=data
            )
            verb = "Created" if created else "Updated"
            self.stdout.write(f"{verb} category: {category.name}")

        for group_name in GROUPS:
            group, created = Group.objects.get_or_create(name=group_name)
            verb = "Created" if created else "Already exists"
            self.stdout.write(f"{verb} group: {group.name}")

        for venue_data in VENUES:
            section_names = venue_data.pop("sections", [])
            venue, created = Venue.objects.update_or_create(
                name=venue_data["name"], defaults=venue_data
            )
            verb = "Created" if created else "Updated"
            self.stdout.write(f"{verb} venue: {venue.name}")

            for section_name in section_names:
                section, created = Section.objects.update_or_create(
                    venue=venue, name=section_name
                )
                verb = "Created" if created else "Already exists"
                self.stdout.write(f"  {verb} section: {section.name}")

        self.stdout.write(self.style.SUCCESS("Seed data applied."))
