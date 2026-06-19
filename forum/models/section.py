from django.db import models

from core.models import BaseModel


class Section(BaseModel):
    venue = models.ForeignKey("forum.Venue", on_delete=models.CASCADE, related_name="sections")
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["venue", "name"]
        unique_together = ["venue", "name"]

    def __str__(self):
        return f"{self.venue.name} - {self.name}"
