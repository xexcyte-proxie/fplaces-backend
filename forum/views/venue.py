from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions

from core.viewsets import BaseViewSet
from forum.filters import VenueFilter
from forum.models import Venue
from forum.serializers import VenueSerializer

_TAGS = ["Venues"]


@extend_schema_view(
    list=extend_schema(
        tags=_TAGS,
        summary="List venues",
        description="Returns stadiums/arenas fans can select to join a live feed. Public "
        "endpoint, so a venue picker can be shown before login. Selecting a venue is a "
        "required onboarding step — the social feed (`/api/forum/posts/`) and its "
        "WebSocket room (`ws/venues/<id>/`) are both scoped to a single venue.",
    ),
    retrieve=extend_schema(tags=_TAGS, summary="Retrieve a venue"),
    create=extend_schema(
        tags=["Admin"],
        summary="Create a venue (admin only)",
        description="Venue Admin / backend-operator action — venues aren't "
        "user-creatable. `latitude`/`longitude` are optional and reserved for a future "
        "GPS auto-suggest feature.",
    ),
    update=extend_schema(tags=["Admin"], summary="Replace a venue (admin only)"),
    partial_update=extend_schema(tags=["Admin"], summary="Update a venue (admin only)"),
    destroy=extend_schema(
        tags=["Admin"],
        summary="Archive a venue (admin only)",
        description="Soft-delete only — existing posts/sections keep their `venue` "
        "reference.",
    ),
    restore=extend_schema(tags=["Admin"], summary="Restore an archived venue (admin only)"),
)
class VenueViewSet(BaseViewSet):
    queryset = Venue.objects.all()
    serializer_class = VenueSerializer
    filterset_class = VenueFilter
    ordering = ["name"]
    ordering_fields = ["name", "created_at"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]
