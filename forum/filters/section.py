import django_filters

from core.filters import BaseFilterSet
from forum.models import Section


class SectionFilter(BaseFilterSet):
    venue = django_filters.NumberFilter(field_name="venue_id")
    floor = django_filters.NumberFilter(field_name="floor_id")

    class Meta:
        model = Section
        fields = ["venue", "floor", "is_active"]
