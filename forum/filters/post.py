import django_filters

from core.filters import BaseFilterSet
from forum.models import Post


class PostFilter(BaseFilterSet):
    venue = django_filters.NumberFilter(field_name="venue_id")
    category = django_filters.NumberFilter(field_name="category_id")
    section = django_filters.NumberFilter(field_name="section_id")
    latest = django_filters.BooleanFilter(method="filter_latest")

    class Meta:
        model = Post
        fields = ["venue", "category", "section", "status"]

    def filter_latest(self, queryset, name, value):
        if value:
            return queryset.order_by("-created_at")
        return queryset
