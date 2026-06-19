from core.serializers import BaseSerializer
from forum.models import Section


class SectionSerializer(BaseSerializer):
    class Meta:
        model = Section
        fields = ["id", "venue", "name", "code", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id"]
        extra_kwargs = {
            "venue": {"help_text": "The venue this section belongs to."},
            "name": {"help_text": "e.g. 'North Stand', 'VIP'. Unique per venue."},
            "code": {"help_text": "Optional short code for the section, e.g. a gate/seat-map label."},
            "is_active": {
                "help_text": "Toggle off to temporarily close a section (e.g. for an "
                "event) without archiving its post history."
            },
        }
