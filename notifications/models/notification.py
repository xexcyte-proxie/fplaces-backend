from django.db import models

from core.models import BaseModel


class Notification(BaseModel):
    VERB_COMMENT = "comment"
    VERB_UPVOTE = "upvote"
    VERB_MODERATION = "moderation"
    VERB_BROADCAST = "broadcast"
    VERB_CHOICES = [
        (VERB_COMMENT, "Comment"),
        (VERB_UPVOTE, "Upvote"),
        (VERB_MODERATION, "Moderation"),
        (VERB_BROADCAST, "Broadcast"),
    ]

    recipient = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="notifications"
    )
    actor = models.ForeignKey(
        "users.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    verb = models.CharField(max_length=20, choices=VERB_CHOICES)
    post = models.ForeignKey(
        "forum.Post", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    comment = models.ForeignKey(
        "forum.Comment", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.verb} -> {self.recipient}"
