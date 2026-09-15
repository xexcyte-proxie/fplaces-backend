from django.db import models

from core.models import BaseModel


class LocationMessage(BaseModel):
    conversation = models.ForeignKey("forum.LocationConversation", on_delete=models.CASCADE, related_name="messages")
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="location_messages")
    content = models.TextField(max_length=500)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user}: {self.content[:30]}"
