import django_filters

from core.filters import BaseFilterSet
from forum.models import Floor


class FloorFilter(BaseFilterSet):
    venue = django_filters.NumberFilter(field_name="venue_id")

    class Meta:
        model = Floor
        fields = ["venue"]
