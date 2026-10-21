from core.serializers import BaseSerializer
from forum.models import Floor


class FloorSerializer(BaseSerializer):
    class Meta:
        model = Floor
        fields = [
            "id",
            "venue",
            "mappedin_floor_id",
            "name",
            "elevation",
            "order",
            "raw_json",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "mappedin_floor_id", "elevation", "raw_json"]
        extra_kwargs = {
            "venue": {"help_text": "The venue this floor belongs to."},
            "name": {
                "help_text": "e.g. 'Level 1', 'Main Concourse'. Synced from Mappedin."
            },
            "order": {
                "help_text": "Display order within the venue, ascending (lowest floor first)."
            },
        }
