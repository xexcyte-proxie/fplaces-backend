import django_filters

from core.filters import BaseFilterSet
from forum.models import Interest


class InterestFilter(BaseFilterSet):
    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")

    class Meta:
        model = Interest
        fields = ["name", "is_active"]
