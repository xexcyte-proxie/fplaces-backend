from django.db import models

from core.models import BaseModel


class Venue(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    location = models.CharField(max_length=255, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    mappedin_key = models.CharField(max_length=255, null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
