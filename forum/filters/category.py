import django_filters

from core.filters import BaseFilterSet
from forum.models import Category


class CategoryFilter(BaseFilterSet):
    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")

    class Meta:
        model = Category
        fields = ["name", "is_active"]
