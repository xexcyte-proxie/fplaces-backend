from django.db import models

from core.models import BaseModel


class LocationConversation(BaseModel):
    venue = models.ForeignKey(
        "forum.Venue", on_delete=models.CASCADE, related_name="location_conversations"
    )
    location_id = models.CharField(max_length=255)
    location_name = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ["venue", "location_id"]

    def __str__(self):
        return f"{self.venue.name} - {self.location_id}"
