from django.conf import settings
from django.db import models

from core.managers import BaseManager


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_archived = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="%(app_label)s_%(class)s_created",
    )

    objects = BaseManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    def archive(self):
        self.is_archived = True
        self.save(update_fields=["is_archived", "updated_at"])

    def restore(self):
        self.is_archived = False
        self.save(update_fields=["is_archived", "updated_at"])
