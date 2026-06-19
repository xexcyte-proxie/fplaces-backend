from rest_framework import serializers

from core.serializers import BaseSerializer
from forum.models import Post
from users.serializers import PublicUserSerializer


class PostSerializer(BaseSerializer):
    user = PublicUserSerializer(read_only=True)
    has_upvoted = serializers.SerializerMethodField(
        help_text="Whether the requesting user has currently upvoted this post."
    )

    class Meta:
        model = Post
        fields = [
            "id",
            "user",
            "venue",
            "section",
            "category",
            "content",
            "upvotes_count",
            "flags_count",
            "status",
            "has_upvoted",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "upvotes_count", "flags_count", "status"]
        extra_kwargs = {
            "venue": {"help_text": "The venue this post belongs to. Required."},
            "section": {
                "help_text": "Optional physical section within the venue (e.g. North "
                "Stand). Drives the live section heatmap when set."
            },
            "category": {"help_text": "One of the fixed post categories (see /api/forum/categories/)."},
            "content": {"help_text": "Post text, max 140 characters."},
        }

    def get_has_upvoted(self, obj) -> bool:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.votes.filter(user=request.user, is_archived=False).exists()
