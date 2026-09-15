from rest_framework import serializers

from core.serializers import BaseSerializer
from forum.models import LocationMessage
from users.serializers import PublicUserSerializer


class LocationMessageCreateSerializer(serializers.Serializer):
    """Input-only shape for `POST /api/forum/conversations/`. `venue`/`location_id`/
    `location_name` belong to the conversation (channel), not the message, so this isn't
    a ModelSerializer over either model — the view resolves the channel (find-or-create)
    before building the actual `LocationMessage` row."""

    venue = serializers.IntegerField(
        help_text="Venue id. Must exist (and not be archived) or a 404 is raised."
    )
    location_id = serializers.CharField(
        max_length=255,
        allow_blank=False,
        help_text="Opaque Mappedin location/place id, exact match. Never slugified or rewritten.",
    )
    location_name = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        default="",
        help_text="Display name for the conversation. Only used on first create (or to "
        "backfill a currently-blank name); ignored once the conversation already has one.",
    )
    content = serializers.CharField(
        max_length=500, allow_blank=False, help_text="Message text, 1-500 characters."
    )


class LocationMessageSerializer(BaseSerializer):
    venue = serializers.IntegerField(source="conversation.venue_id", read_only=True)
    location_id = serializers.CharField(
        source="conversation.location_id", read_only=True
    )
    location_name = serializers.CharField(
        source="conversation.location_name", read_only=True
    )
    user = PublicUserSerializer(read_only=True)

    class Meta:
        model = LocationMessage
        fields = [
            "id",
            "venue",
            "location_id",
            "location_name",
            "user",
            "content",
            "created_at",
            "updated_at",
        ]
        # Only `content` is writable, and only via PATCH/PUT on an existing message
        # (create() is handled separately by LocationMessageCreateSerializer since it
        # needs to resolve/create the parent conversation first).
        read_only_fields = ["id", "venue", "location_id", "location_name", "user"]
        extra_kwargs = {"content": {"help_text": "Message text, max 500 characters."}}
