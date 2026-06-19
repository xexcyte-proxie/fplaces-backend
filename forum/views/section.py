from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import permissions

from core.viewsets import BaseViewSet
from forum.filters import SectionFilter
from forum.models import Section
from forum.serializers import SectionSerializer

_TAGS = ["Sections"]


@extend_schema_view(
    list=extend_schema(
        tags=_TAGS,
        summary="List sections",
        description="Physical zones within a venue (e.g. North Stand, South Stand, VIP). "
        "Posts can optionally tag a section, which drives the live section heatmap "
        "(`section_heat_update` events on the venue's WebSocket room). Public endpoint; "
        "filter by venue with `?venue=<id>`.",
        parameters=[
            OpenApiParameter(
                "venue", int, description="Filter to sections belonging to this venue id."
            ),
        ],
    ),
    retrieve=extend_schema(tags=_TAGS, summary="Retrieve a section"),
    create=extend_schema(
        tags=["Admin"],
        summary="Create a section (admin only)",
        description="`(venue, name)` must be unique.",
    ),
    update=extend_schema(tags=["Admin"], summary="Replace a section (admin only)"),
    partial_update=extend_schema(
        tags=["Admin"],
        summary="Update a section (admin only)",
        description="Commonly used to toggle `is_active` for a section that's "
        "temporarily closed for an event, without archiving its post history.",
    ),
    destroy=extend_schema(
        tags=["Admin"],
        summary="Archive a section (admin only)",
        description="Soft-delete only. Posts referencing an archived section keep "
        "their reference (`on_delete=SET_NULL` only applies if the section is hard "
        "deleted, which this endpoint never does).",
    ),
    restore=extend_schema(tags=["Admin"], summary="Restore an archived section (admin only)"),
)
class SectionViewSet(BaseViewSet):
    queryset = Section.objects.all()
    serializer_class = SectionSerializer
    filterset_class = SectionFilter
    ordering = ["venue", "name"]
    ordering_fields = ["name", "created_at"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]
