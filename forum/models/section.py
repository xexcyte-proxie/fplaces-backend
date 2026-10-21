from django.db import models

from core.models import BaseModel


class Section(BaseModel):
    venue = models.ForeignKey(
        "forum.Venue", on_delete=models.CASCADE, related_name="sections"
    )
    floor = models.ForeignKey(
        "forum.Floor",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="sections",
        help_text="The floor this section is on, if synced from Mappedin. Null for sections "
        "created directly by an admin.",
    )
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=20, blank=True)
    mappedin_location_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="Mappedin location id ('loc_...') this section was synced from, if any. Used as the stable "
        "match key when re-syncing a floor, since names alone aren't unique across floors (e.g. 'Restroom' "
        "commonly appears on every floor).",
    )
    is_active = models.BooleanField(default=True)
    raw_json = models.JSONField(
        null=True,
        blank=True,
        help_text="Raw location object as last returned by Mappedin's MVF export.",
    )

    class Meta:
        ordering = ["venue", "name"]
        unique_together = ["floor", "mappedin_location_id"]

    def __str__(self):
        return f"{self.venue.name} - {self.name}"
