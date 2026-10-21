from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from loguru import logger

from forum.models import Venue
from forum.services.mappedin_sync import sync_venue_from_mappedin


@receiver(pre_save, sender=Venue)
def _stash_old_mappedin_map_id(sender, instance, **kwargs):
    """Stashes the DB's current mappedin_map_id on the instance so post_save can tell
    whether it actually changed. Needed because Django doesn't otherwise expose the
    pre-update value in post_save, and callers (DRF serializers, the admin, etc.)
    don't reliably pass save(update_fields=...) for us to check instead."""
    if instance.pk:
        instance._old_mappedin_map_id = (
            Venue.objects.filter(pk=instance.pk)
            .values_list("mappedin_map_id", flat=True)
            .first()
        )
    else:
        instance._old_mappedin_map_id = None


@receiver(post_save, sender=Venue)
def sync_venue_from_mappedin_on_save(sender, instance, created, **kwargs):
    """Triggers a Mappedin sync (see forum.services.mappedin_sync) whenever a venue's
    mappedin_map_id is set or changed. Runs synchronously (no task queue exists in this
    project, and venue edits are infrequent admin actions) — a Mappedin failure is logged
    and swallowed rather than raised, so an outage there never blocks saving a venue.
    """
    if not instance.mappedin_map_id:
        return

    old_value = getattr(instance, "_old_mappedin_map_id", None)
    if not created and old_value == instance.mappedin_map_id:
        return

    try:
        result = sync_venue_from_mappedin(instance)
    except Exception:
        logger.exception(f"Failed to sync venue {instance.id} from Mappedin")
        return

    if not result["venue_found"]:
        logger.warning(
            f"Venue {instance.id}: mappedin_map_id {instance.mappedin_map_id!r} not found "
            "in Mappedin's venue list — latitude/longitude/raw_json not updated."
        )

    logger.info(
        f"Synced {result['floors_count']} floor(s), {result['sections_count']} section(s) "
        f"from Mappedin for venue {instance.id} ({instance.name})"
    )
