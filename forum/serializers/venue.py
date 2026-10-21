from core.serializers import BaseSerializer
from forum.models import Venue


class VenueSerializer(BaseSerializer):
    class Meta:
        model = Venue
        fields = [
            "id",
            "name",
            "location",
            "latitude",
            "longitude",
            "mappedin_map_id",
            "raw_json",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "raw_json"]
        extra_kwargs = {
            "name": {"help_text": "Display name, must be unique."},
            "location": {"help_text": "Free-text address/location."},
            "latitude": {
                "help_text": "Auto-populated from Mappedin whenever mappedin_map_id is set or "
                "changed. Can still be set manually for a venue with no Mappedin integration."
            },
            "longitude": {
                "help_text": "Auto-populated from Mappedin whenever mappedin_map_id is set or "
                "changed. Can still be set manually for a venue with no Mappedin integration."
            },
            "mappedin_map_id": {
                "help_text": "Mappedin venue id. Setting or changing this triggers an automatic "
                "sync of latitude/longitude, floors, and sections from Mappedin."
            },
        }
