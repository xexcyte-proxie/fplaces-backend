from core.serializers import BaseSerializer
from forum.models import Category


class CategorySerializer(BaseSerializer):
    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "disclaimer",
            "order",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug"]
        extra_kwargs = {
            "name": {"help_text": "Display name, must be unique."},
            "slug": {"help_text": "Auto-derived from `name` if not provided."},
            "description": {"help_text": "Short explanation shown under the category in pickers."},
            "disclaimer": {
                "help_text": "Optional warning shown when this category is selected, e.g. "
                "the Help category's medical/security disclaimer."
            },
            "order": {"help_text": "Sort order in category pickers, ascending."},
            "is_active": {"help_text": "Toggle off to hide from new-post pickers without affecting existing posts."},
        }
