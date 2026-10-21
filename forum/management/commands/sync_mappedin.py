from django.core.management.base import BaseCommand, CommandError

from forum.models import Venue
from forum.services.mappedin_sync import sync_venue_from_mappedin


class Command(BaseCommand):
    help = (
        "Syncs latitude/longitude/raw_json, floors, and sections from Mappedin for one "
        "venue (by id) or every venue with a mappedin_map_id set."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "venue_id",
            nargs="?",
            type=int,
            help="Sync only this venue's database id. Omit to sync every venue with a mappedin_map_id.",
        )

    def handle(self, *args, **options):
        venue_id = options.get("venue_id")

        if venue_id:
            try:
                venues = [Venue.objects.get(pk=venue_id)]
            except Venue.DoesNotExist:
                raise CommandError(f"No venue with id={venue_id}")
        else:
            venues = list(
                Venue.objects.exclude(mappedin_map_id__isnull=True).exclude(
                    mappedin_map_id=""
                )
            )

        if not venues:
            self.stdout.write(
                self.style.WARNING("No venues with a mappedin_map_id to sync.")
            )
            return

        synced, failed = 0, 0
        for venue in venues:
            if not venue.mappedin_map_id:
                self.stdout.write(
                    self.style.WARNING(
                        f"Skipping {venue.name} (id={venue.id}): no mappedin_map_id set."
                    )
                )
                continue

            self.stdout.write(
                f"Syncing {venue.name} (id={venue.id}, mappedin_map_id={venue.mappedin_map_id})..."
            )
            try:
                result = sync_venue_from_mappedin(venue)
            except Exception as exc:
                failed += 1
                self.stderr.write(self.style.ERROR(f"  Failed: {exc}"))
                continue

            if not result["venue_found"]:
                self.stdout.write(
                    self.style.WARNING(
                        "  mappedin_map_id not found in Mappedin's venue list — "
                        "latitude/longitude/raw_json not updated, but floors/sections still synced "
                        "if the MVF export worked."
                    )
                )

            synced += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f"  Synced {result['floors_count']} floor(s), {result['sections_count']} section(s)."
                )
            )

        self.stdout.write(
            f"\nDone: {synced} synced, {failed} failed, {len(venues)} total."
        )
