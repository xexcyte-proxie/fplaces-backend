from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import permissions

from core.permissions import IsOwnerOrReadOnly
from core.realtime import broadcast, venue_group
from core.viewsets import BaseViewSet
from forum.filters import CommentFilter
from forum.models import Comment
from forum.serializers import CommentSerializer
from notifications.models import Notification
from notifications.services.notify import notify

_TAGS = ["Comments"]


@extend_schema_view(
    list=extend_schema(
        tags=_TAGS,
        summary="List comments",
        description="Filter to a single post's thread with `?post=<id>`. Comments are "
        "a flat (1-level) thread per post, ordered oldest first.",
        parameters=[
            OpenApiParameter("post", int, description="Filter to comments on this post."),
        ],
    ),
    retrieve=extend_schema(tags=_TAGS, summary="Retrieve a comment"),
    create=extend_schema(
        tags=_TAGS,
        summary="Create a comment",
        description="`user` is set from the authenticated requester. Creating a "
        "comment broadcasts a `new_comment` event to the post's venue WebSocket room, "
        "and creates a `comment` notification for the post's author (pushed live to "
        "their `ws/notifications/` socket) unless they're commenting on their own post.",
    ),
    update=extend_schema(
        tags=_TAGS, summary="Replace a comment", description="Only the comment's own author or staff may edit it."
    ),
    partial_update=extend_schema(
        tags=_TAGS,
        summary="Update a comment",
        description="Only the comment's own author or staff may edit it.",
    ),
    destroy=extend_schema(
        tags=_TAGS,
        summary="Archive a comment (soft delete)",
        description="Only the comment's own author or staff may delete it.",
    ),
    restore=extend_schema(tags=_TAGS, summary="Restore an archived comment"),
)
class CommentViewSet(BaseViewSet):
    queryset = Comment.objects.select_related("user", "post")
    serializer_class = CommentSerializer
    filterset_class = CommentFilter
    ordering = ["created_at"]
    ordering_fields = ["created_at"]

    def get_permissions(self):
        if self.action in ["update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated(), IsOwnerOrReadOnly()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        comment = serializer.save(user=self.request.user)

        broadcast(
            venue_group(comment.post.venue_id),
            "new_comment",
            self.get_serializer(comment).data,
        )

        notify(
            recipient=comment.post.user,
            actor=comment.user,
            verb=Notification.VERB_COMMENT,
            post=comment.post,
            comment=comment,
            message=f"{comment.user.display_name} commented on your post.",
        )
