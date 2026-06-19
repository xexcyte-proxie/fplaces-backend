from core.serializers import BaseSerializer
from forum.models import Comment
from users.serializers import PublicUserSerializer


class CommentSerializer(BaseSerializer):
    user = PublicUserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "post", "user", "content", "created_at", "updated_at"]
        read_only_fields = ["id", "user"]
        extra_kwargs = {
            "post": {"help_text": "The post this comment replies to."},
            "content": {"help_text": "Comment text, max 500 characters."},
        }
