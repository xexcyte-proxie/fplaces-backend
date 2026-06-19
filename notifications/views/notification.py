from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer
from rest_framework import mixins, permissions, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.serializers import DetailResponseSerializer
from notifications.models import Notification
from notifications.serializers import NotificationSerializer


@extend_schema_view(
    list=extend_schema(
        tags=["Notifications"],
        summary="List my notifications",
        description="Returns the authenticated user's notifications, newest first. The "
        "same events are also pushed live over the `ws/notifications/` WebSocket as "
        "they're created, so clients typically combine an initial fetch here with "
        "live updates from the socket rather than polling.",
    ),
    retrieve=extend_schema(
        tags=["Notifications"],
        summary="Retrieve a single notification",
    ),
)
class NotificationViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    ordering = ["-created_at"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Notification.objects.none()
        return Notification.objects.filter(recipient=self.request.user)

    @extend_schema(
        tags=["Notifications"],
        summary="Get my unread notification count",
        description="Lightweight count endpoint for rendering a notification badge "
        "without paginating through the full list.",
        responses={
            200: inline_serializer(
                name="UnreadCount", fields={"unread_count": serializers.IntegerField()}
            )
        },
    )
    @action(detail=False, methods=["get"])
    def unread_count(self, request):
        count = self.get_queryset().filter(is_read=False).count()
        return Response({"unread_count": count})

    @extend_schema(
        tags=["Notifications"],
        summary="Mark all my notifications as read",
        request=None,
        responses={200: DetailResponseSerializer},
    )
    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({"detail": "All notifications marked as read."})

    @extend_schema(
        tags=["Notifications"],
        summary="Mark one notification as read",
        request=None,
        responses={200: NotificationSerializer},
    )
    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=["is_read", "updated_at"])
        return Response(self.get_serializer(notification).data)
