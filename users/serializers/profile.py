from django.contrib.auth import get_user_model
from django.db.models import Sum
from rest_framework import serializers

from core.serializers import BaseSerializer

User = get_user_model()


class UserSerializer(BaseSerializer):
    interests = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_null=True,
        help_text="List of user interests.",
    )
    stat = serializers.SerializerMethodField(
        help_text="Aggregate profile stats: `posts_count` (posts authored), "
        "`upvotes_count` (upvotes received across those posts), and `venues_count` "
        "(distinct venues posted in)."
    )
    recent_posts = serializers.SerializerMethodField(
        help_text="The user's 5 most recently created posts, newest first."
    )

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "pseudo_name",
            "first_name",
            "last_name",
            "bio",
            "avatar_url",
            "user_type",
            "is_email_verified",
            "interests",
            "stat",
            "recent_posts",
            "created_at",
            "updated_at",
        ]

        read_only_fields = ["id", "email", "user_type", "is_email_verified"]
        extra_kwargs = {
            "pseudo_name": {
                "help_text": "Public display name shown on posts/comments instead of "
                "the user's real email. Must be unique. Set this during onboarding, "
                "after email verification and before selecting a venue."
            },
        }

    def get_stat(self, obj):
        posts = obj.posts.filter(is_archived=False)
        return {
            "posts_count": posts.count(),
            "upvotes_count": posts.aggregate(total=Sum("upvotes_count"))["total"] or 0,
            "venues_count": posts.values("venue_id").distinct().count(),
        }

    def get_recent_posts(self, obj):
        from forum.serializers import PostSerializer

        recent_posts = obj.posts.filter(is_archived=False).order_by("-created_at")[:5]
        return PostSerializer(recent_posts, many=True, context=self.context).data


class PublicUserSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(
        read_only=True,
        help_text="`pseudo_name` if set, otherwise falls back to the email's local part.",
    )

    class Meta:
        model = User
        fields = ["id", "display_name"]
