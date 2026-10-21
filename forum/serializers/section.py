from core.serializers import BaseSerializer
from forum.models import Section


class SectionSerializer(BaseSerializer):
    class Meta:
        model = Section
        fields = [
            "id",
            "venue",
            "floor",
            "name",
            "code",
            "mappedin_location_id",
            "raw_json",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "mappedin_location_id", "raw_json"]
        extra_kwargs = {
            "venue": {"help_text": "The venue this section belongs to."},
            "floor": {
                "help_text": "The floor this section is on, if synced from Mappedin. Null for "
                "sections created directly by an admin."
            },
            "name": {
                "help_text": "e.g. 'North Stand', 'VIP'. Unique per floor for Mappedin-synced "
                "sections; names may repeat across floors (e.g. 'Restroom' on every level)."
            },
            "code": {
                "help_text": "Optional short code for the section, e.g. a gate/seat-map label."
            },
            "is_active": {
                "help_text": "Toggle off to temporarily close a section (e.g. for an "
                "event) without archiving its post history."
            },
        }
