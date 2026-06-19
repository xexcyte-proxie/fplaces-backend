from django.db import models

from core.models import BaseModel


class Comment(BaseModel):
    post = models.ForeignKey("forum.Post", on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="comments")
    content = models.TextField(max_length=500)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.user}: {self.content[:30]}"
