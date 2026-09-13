from core.serializers import BaseSerializer
from forum.models import Interest


class InterestSerializer(BaseSerializer):
    class Meta:
        model = Interest
        fields = [
            "id",
            "name",
            "slug",
            "order",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug"]
        extra_kwargs = {
            "name": {"help_text": "Display name, must be unique."},
            "slug": {"help_text": "Auto-derived from `name` if not provided."},
            "order": {"help_text": "Sort order in interest pickers, ascending."},
            "is_active": {"help_text": "Toggle off to hide from interest pickers without affecting users who already selected it."},
        }
