from rest_framework import serializers

from forum.models import Post
from users.serializers import PublicUserSerializer


class AdminPostSerializer(serializers.ModelSerializer):
    user_detail = PublicUserSerializer(source="user", read_only=True)
    venue_name = serializers.CharField(source="venue.name", read_only=True)
    section_name = serializers.CharField(source="section.name", read_only=True, default=None)
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Post
        fields = [
            "id",
            "user",
            "user_detail",
            "venue",
            "venue_name",
            "section",
            "section_name",
            "category",
            "category_name",
            "content",
            "upvotes_count",
            "flags_count",
            "status",
            "is_archived",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "upvotes_count", "flags_count", "created_at", "updated_at"]
        extra_kwargs = {
            "user": {"help_text": "The post's author. Writable here (unlike the public PostSerializer) so admins can create/reassign posts on a user's behalf."},
            "venue": {"help_text": "The venue this post belongs to."},
            "section": {"help_text": "Optional section within the venue."},
            "category": {"help_text": "One of the fixed post categories."},
            "status": {"help_text": "`visible` or `hidden`. Prefer the `hide`/`show` actions over editing this directly so the `post_hidden` WebSocket event fires."},
        }
