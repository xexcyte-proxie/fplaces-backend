from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import permissions

from core.permissions import IsOwnerOrReadOnly
from core.realtime import broadcast, section_group
from core.viewsets import BaseViewSet
from forum.filters import SectionMessageFilter
from forum.models import SectionMessage
from forum.serializers import SectionMessageSerializer

_TAGS = ["Section Conversations"]


@extend_schema_view(
    list=extend_schema(
        tags=_TAGS,
        summary="List section conversation messages",
        description="Filter to a single section's conversation with `?section=<id>`. Each "
        "section (e.g. North Stand, VIP) has its own separate conversation, independent of "
        "the venue-wide post feed. Messages are ordered oldest first.",
        parameters=[
            OpenApiParameter("section", int, description="Filter to messages in this section."),
        ],
    ),
    retrieve=extend_schema(tags=_TAGS, summary="Retrieve a section conversation message"),
    create=extend_schema(
        tags=_TAGS,
        summary="Post a message to a section's conversation",
        description="`user` is set from the authenticated requester. Creating a message "
        "broadcasts a `new_section_message` event to the section's WebSocket room "
        "(`ws/sections/<section_id>/`).",
    ),
    update=extend_schema(
        tags=_TAGS,
        summary="Replace a section conversation message",
        description="Only the message's own author or staff may edit it.",
    ),
    partial_update=extend_schema(
        tags=_TAGS,
        summary="Update a section conversation message",
        description="Only the message's own author or staff may edit it.",
    ),
    destroy=extend_schema(
        tags=_TAGS,
        summary="Archive a section conversation message (soft delete)",
        description="Only the message's own author or staff may delete it.",
    ),
    restore=extend_schema(tags=_TAGS, summary="Restore an archived section conversation message"),
)
class SectionMessageViewSet(BaseViewSet):
    queryset = SectionMessage.objects.select_related("user", "section")
    serializer_class = SectionMessageSerializer
    filterset_class = SectionMessageFilter
    ordering = ["created_at"]
    ordering_fields = ["created_at"]

    def get_permissions(self):
        if self.action in ["update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated(), IsOwnerOrReadOnly()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        message = serializer.save(user=self.request.user)

        broadcast(
            section_group(message.section_id),
            "new_section_message",
            self.get_serializer(message).data,
        )
