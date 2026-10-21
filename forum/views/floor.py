from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import permissions

from core.viewsets import BaseViewSet
from forum.filters import FloorFilter
from forum.models import Floor
from forum.serializers import FloorSerializer

_TAGS = ["Floors"]


@extend_schema_view(
    list=extend_schema(
        tags=_TAGS,
        summary="List floors",
        description="A venue's floors/levels, synced automatically from Mappedin whenever its "
        "`mappedin_map_id` is set or changed (see `GET /api/forum/sections/?floor=<id>` for the "
        "named sections on each floor). Public endpoint; filter by venue with `?venue=<id>`.",
        parameters=[
            OpenApiParameter(
                "venue", int, description="Filter to floors belonging to this venue id."
            ),
        ],
    ),
    retrieve=extend_schema(tags=_TAGS, summary="Retrieve a floor"),
    create=extend_schema(
        tags=["Admin"],
        summary="Create a floor manually (admin only)",
        description="Floors are normally created automatically by the Mappedin sync. Use this "
        "only to add a floor for a venue with no Mappedin integration.",
    ),
    update=extend_schema(tags=["Admin"], summary="Replace a floor (admin only)"),
    partial_update=extend_schema(
        tags=["Admin"],
        summary="Update a floor (admin only)",
        description="Commonly used to rename a floor or adjust its display `order` after syncing.",
    ),
    destroy=extend_schema(
        tags=["Admin"],
        summary="Archive a floor (admin only)",
        description="Soft-delete only. Sections on an archived floor keep their reference "
        "(`on_delete=SET_NULL` only applies if the floor is hard deleted, which this endpoint never does).",
    ),
    restore=extend_schema(
        tags=["Admin"], summary="Restore an archived floor (admin only)"
    ),
)
class FloorViewSet(BaseViewSet):
    queryset = Floor.objects.all()
    serializer_class = FloorSerializer
    filterset_class = FloorFilter
    ordering = ["venue", "order"]
    ordering_fields = ["order", "elevation", "created_at"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]
