from django.db import models

from core.models import BaseModel


class PostVote(BaseModel):
    post = models.ForeignKey("forum.Post", on_delete=models.CASCADE, related_name="votes")
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="post_votes")

    class Meta:
        unique_together = ["post", "user"]

    def __str__(self):
        return f"{self.user} upvoted {self.post_id}"
