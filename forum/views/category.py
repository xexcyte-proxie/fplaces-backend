from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions

from core.viewsets import BaseViewSet
from forum.filters import CategoryFilter
from forum.models import Category
from forum.serializers import CategorySerializer

_TAGS = ["Categories"]


@extend_schema_view(
    list=extend_schema(
        tags=_TAGS,
        summary="List post categories",
        description="Returns the fixed set of categories fans pick from before posting: "
        "Lines and Crowds, Food and Drinks, Fan Vibe, and Help. Public endpoint — no "
        "authentication required, so a category picker can be shown before login. "
        "Filter with `?is_active=true` to hide retired categories without affecting "
        "historical posts that still reference them.",
    ),
    retrieve=extend_schema(tags=_TAGS, summary="Retrieve a category"),
    create=extend_schema(
        tags=["Admin"],
        summary="Create a category (admin only)",
        description="`slug` is auto-derived from `name` if omitted. Admin-only since "
        "the category list is meant to stay small and curated.",
    ),
    update=extend_schema(tags=["Admin"], summary="Replace a category (admin only)"),
    partial_update=extend_schema(tags=["Admin"], summary="Update a category (admin only)"),
    destroy=extend_schema(
        tags=["Admin"],
        summary="Archive a category (admin only)",
        description="Soft-delete only — existing posts keep their `category` reference "
        "(`on_delete=PROTECT` at the DB level prevents hard deletion anyway).",
    ),
    restore=extend_schema(tags=["Admin"], summary="Restore an archived category (admin only)"),
)
class CategoryViewSet(BaseViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filterset_class = CategoryFilter
    ordering = ["order", "name"]
    ordering_fields = ["order", "name", "created_at"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]
