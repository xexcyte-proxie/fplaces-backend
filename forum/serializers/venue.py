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
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id"]
        extra_kwargs = {
            "name": {"help_text": "Display name, must be unique."},
            "location": {"help_text": "Free-text address/location."},
            "latitude": {"help_text": "Reserved for future GPS auto-suggest."},
            "longitude": {"help_text": "Reserved for future GPS auto-suggest."},
        }
