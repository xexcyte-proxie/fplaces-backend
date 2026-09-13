import django_filters

from core.filters import BaseFilterSet
from forum.models import SectionMessage


class SectionMessageFilter(BaseFilterSet):
    section = django_filters.NumberFilter(field_name="section_id")

    class Meta:
        model = SectionMessage
        fields = ["section"]
