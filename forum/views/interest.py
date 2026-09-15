from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions

from core.viewsets import BaseViewSet
from forum.filters import InterestFilter
from forum.models import Interest
from forum.serializers import InterestSerializer

_TAGS = ["Interests"]


@extend_schema_view(
    list=extend_schema(
        tags=_TAGS,
        summary="List interests",
        description="Returns the curated catalog of interests fans can pick from on their "
        "profile, replacing what was previously hardcoded on the frontend. Public endpoint — "
        "no authentication required. Filter with `?is_active=true` to hide retired interests "
        "without affecting users who already selected them.",
    ),
    retrieve=extend_schema(tags=_TAGS, summary="Retrieve an interest"),
    create=extend_schema(
        tags=["Admin"],
        summary="Create an interest (admin only)",
        description="`slug` is auto-derived from `name` if omitted.",
    ),
    update=extend_schema(tags=["Admin"], summary="Replace an interest (admin only)"),
    partial_update=extend_schema(
        tags=["Admin"], summary="Update an interest (admin only)"
    ),
    destroy=extend_schema(tags=["Admin"], summary="Archive an interest (admin only)"),
    restore=extend_schema(
        tags=["Admin"], summary="Restore an archived interest (admin only)"
    ),
)
class InterestViewSet(BaseViewSet):
    queryset = Interest.objects.all()
    serializer_class = InterestSerializer
    filterset_class = InterestFilter
    ordering = ["order", "name"]
    ordering_fields = ["order", "name", "created_at"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]
