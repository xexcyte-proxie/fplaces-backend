from django.db import models

from core.managers import BaseManager


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_archived = models.BooleanField(default=False)

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
