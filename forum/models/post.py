from django.db import models

from core.models import BaseModel


class Post(BaseModel):
    STATUS_VISIBLE = "visible"
    STATUS_HIDDEN = "hidden"
    STATUS_CHOICES = [
        (STATUS_VISIBLE, "Visible"),
        (STATUS_HIDDEN, "Hidden"),
    ]

    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="posts")
    venue = models.ForeignKey("forum.Venue", on_delete=models.CASCADE, related_name="posts")
    section = models.ForeignKey(
        "forum.Section", on_delete=models.SET_NULL, null=True, blank=True, related_name="posts"
    )
    category = models.ForeignKey("forum.Category", on_delete=models.PROTECT, related_name="posts")

    content = models.CharField(max_length=140)

    upvotes_count = models.PositiveIntegerField(default=0)
    flags_count = models.PositiveIntegerField(default=0)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_VISIBLE)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user}: {self.content[:30]}"
