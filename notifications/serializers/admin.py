from rest_framework import serializers


class AdminNotificationRequestSerializer(serializers.Serializer):
    CHANNEL_EMAIL = "email"
    CHANNEL_PUSH = "push"
    CHANNEL_CHOICES = [
        (CHANNEL_EMAIL, "Email"),
        (CHANNEL_PUSH, "Push"),
    ]

    subject = serializers.CharField(
        max_length=100,
        help_text="Subject of the notification (required, especially for email templates).",
    )
    message = serializers.CharField(
        max_length=1000,
        help_text="Body content of the notification.",
    )
    channels = serializers.MultipleChoiceField(
        choices=CHANNEL_CHOICES,
        help_text="Delivery channels (email, push, or both).",
    )
    venue = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="Filter users by venue they have posted in.",
    )
    section = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="Filter users by section they have posted in.",
    )
    category = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="Filter users by category they have posted in.",
    )
    users = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
        help_text="List of specific user IDs to notify.",
    )

    def validate(self, attrs):
        venue = attrs.get("venue")
        section = attrs.get("section")
        category = attrs.get("category")
        users = attrs.get("users")

        if not any([venue, section, category, users]):
            raise serializers.ValidationError(
                "At least one target filter (venue, section, category, or users) must be provided."
            )
        return attrs
