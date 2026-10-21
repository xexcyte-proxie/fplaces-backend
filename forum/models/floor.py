from django.db import models

from core.models import BaseModel


class Floor(BaseModel):
    venue = models.ForeignKey(
        "forum.Venue", on_delete=models.CASCADE, related_name="floors"
    )
    mappedin_floor_id = models.CharField(
        max_length=255, help_text="Mappedin map id for this floor, e.g. 'm_...'."
    )
    name = models.CharField(max_length=100, blank=True)
    elevation = models.IntegerField(null=True, blank=True)
    order = models.PositiveIntegerField(default=0)
    raw_json = models.JSONField(
        null=True,
        blank=True,
        help_text="Raw floor ('map') object as last returned by Mappedin's MVF export.",
    )

    class Meta:
        ordering = ["venue", "order"]
        unique_together = ["venue", "mappedin_floor_id"]

    def __str__(self):
        return f"{self.venue.name} - {self.name or self.mappedin_floor_id}"
