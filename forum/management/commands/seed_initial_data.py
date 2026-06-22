from random import seed
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from forum.models import Category, Section, Venue

User = get_user_model()

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

VENUES = [
    {
        "name": "Riverside Stadium",
        "location": "1 Riverside Way",
        "sections": ["North Stand", "South Stand", "VIP"],
    },
]


class Command(BaseCommand):
    help = "Seed initial reference data: post categories, base users, and a sample venue."

    def handle(self, *args, **options):
        self.stdout.write("Seeding sample users...")
        users_data = [
            {"email": "admin@fplaces.com", "is_staff": True, "is_superuser": True, "is_email_verified": True, "user_type": User.UserType.ADMIN},
            {"email": "fan@fplaces.com", "is_email_verified": True, "user_type": User.UserType.REGULAR_USER},
        ]
        
        admin_user = None
        for u_data in users_data:
            email = u_data["email"]
            user, created = User.objects.get_or_create(email=email, defaults=u_data)
            if created:
                user.set_password("password123")
                user.save()
            if email == "admin@fplaces.com":
                admin_user = user
            verb = "Created" if created else "Already exists"
            self.stdout.write(f"{verb} user: {email}")

        for data in CATEGORIES:
            data_defaults = data.copy()
            data_defaults["created_by"] = admin_user
            category, created = Category.objects.update_or_create(
                name=data["name"], defaults=data_defaults
            )
            verb = "Created" if created else "Updated"
            self.stdout.write(f"{verb} category: {category.name}")

        for venue_data in VENUES:
            section_names = venue_data.pop("sections", [])
            venue_data["created_by"] = admin_user
            venue, created = Venue.objects.update_or_create(
                name=venue_data["name"], defaults=venue_data
            )
            verb = "Created" if created else "Updated"
            self.stdout.write(f"{verb} venue: {venue.name}")

            for section_name in section_names:
                section, created = Section.objects.update_or_create(
                    venue=venue, name=section_name, defaults={"created_by": admin_user}
                )
                verb = "Created" if created else "Already exists"
                self.stdout.write(f"  {verb} section: {section.name}")

        self.stdout.write(self.style.SUCCESS("Seed data applied."))

