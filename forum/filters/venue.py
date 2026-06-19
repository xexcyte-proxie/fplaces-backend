import django_filters

from core.filters import BaseFilterSet
from forum.models import Venue


class VenueFilter(BaseFilterSet):
    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")

    class Meta:
        model = Venue
        fields = ["name"]
