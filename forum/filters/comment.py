import django_filters

from core.filters import BaseFilterSet
from forum.models import Comment


class CommentFilter(BaseFilterSet):
    post = django_filters.NumberFilter(field_name="post_id")

    class Meta:
        model = Comment
        fields = ["post"]
