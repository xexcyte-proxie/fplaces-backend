from django.contrib.auth import get_user_model
from rest_framework import serializers

from core.serializers import BaseSerializer

User = get_user_model()


class UserSerializer(BaseSerializer):
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


class PublicUserSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(
        read_only=True,
        help_text="`pseudo_name` if set, otherwise falls back to the email's local part.",
    )

    class Meta:
        model = User
        fields = ["id", "display_name"]
