import django_filters

from core.filters import BaseFilterSet
from forum.models import LocationMessage


class LocationMessageFilter(BaseFilterSet):
    venue = django_filters.NumberFilter(field_name="conversation__venue_id")
    location_id = django_filters.CharFilter(field_name="conversation__location_id")

    class Meta:
        model = LocationMessage
        fields = ["venue", "location_id"]
