from django.db import models

from core.models import BaseModel


class PostFlag(BaseModel):
    post = models.ForeignKey("forum.Post", on_delete=models.CASCADE, related_name="flags")
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="post_flags")
    reason = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ["post", "user"]

    def __str__(self):
        return f"{self.user} flagged {self.post_id}"
