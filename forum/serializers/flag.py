from rest_framework import serializers


class PostFlagRequestSerializer(serializers.Serializer):
    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=255,
        help_text="Optional free-text reason for the flag, shown to moderators.",
    )
