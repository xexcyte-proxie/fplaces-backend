from core.serializers import BaseSerializer
from notifications.models import Notification
from users.serializers import PublicUserSerializer


class NotificationSerializer(BaseSerializer):
    actor = PublicUserSerializer(
        read_only=True, help_text="The user whose action triggered this notification, if any."
    )

    class Meta:
        model = Notification
        fields = [
            "id",
            "actor",
            "verb",
            "post",
            "comment",
            "message",
            "is_read",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "actor", "verb", "post", "comment", "message"]
        extra_kwargs = {
            "verb": {"help_text": "Notification type, e.g. `comment` when someone replies to your post."},
            "post": {"help_text": "The related post, if this notification is post-related."},
            "comment": {"help_text": "The related comment, if this notification is comment-related."},
            "message": {"help_text": "Human-readable summary, ready to display as-is."},
            "is_read": {"help_text": "Set via `POST /{id}/mark_read/` or `POST mark_all_read/`."},
        }
