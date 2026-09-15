from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from core.permissions import IsOwnerOrReadOnly
from core.realtime import broadcast_location_message
from core.viewsets import BaseViewSet
from forum.filters import LocationMessageFilter
from forum.models import LocationConversation, LocationMessage, Venue
from forum.serializers import LocationMessageCreateSerializer, LocationMessageSerializer

_TAGS = ["Location Conversations"]


@extend_schema_view(
    list=extend_schema(
        tags=_TAGS,
        summary="List messages for a map location",
        description="Chat scoped to `(venue, location_id)`, where `location_id` is the "
        "opaque Mappedin location/place id the fan tapped on the map — no admin-created "
        "Section required. Both `venue` and `location_id` are required query params. "
        "Returns an empty paginated list (never a 404) if nobody has posted at that "
        "location yet; a conversation is only created on the first `POST`. Newest first.",
        parameters=[
            OpenApiParameter("venue", int, required=True, description="Venue id."),
            OpenApiParameter(
                "location_id",
                str,
                required=True,
                description="Mappedin location id, exact match.",
            ),
        ],
    ),
    retrieve=extend_schema(tags=_TAGS, summary="Retrieve a location message"),
    create=extend_schema(
        tags=_TAGS,
        summary="Post a message to a map location (find-or-create)",
        description="Finds the `(venue, location_id)` conversation, creating it on first "
        "use, then stores the message on it — the client never creates or passes a "
        "conversation id. `location_name` only sets the conversation's display name on "
        "create (or backfills it if currently blank); it's ignored otherwise. Broadcasts "
        "`new_location_message` to `ws/venues/<venue_id>/locations/<location_id>/`.",
        request=LocationMessageCreateSerializer,
        responses={201: LocationMessageSerializer},
    ),
    update=extend_schema(
        tags=_TAGS,
        summary="Replace a location message",
        description="Only the message's own author or staff may edit it.",
    ),
    partial_update=extend_schema(
        tags=_TAGS,
        summary="Update a location message",
        description="Only the message's own author or staff may edit it.",
    ),
    destroy=extend_schema(
        tags=_TAGS,
        summary="Archive a location message (soft delete)",
        description="Only the message's own author or staff may delete it.",
    ),
    restore=extend_schema(tags=_TAGS, summary="Restore an archived location message"),
)
class LocationConversationViewSet(BaseViewSet):
    queryset = LocationMessage.objects.select_related("user", "conversation")
    serializer_class = LocationMessageSerializer
    filterset_class = LocationMessageFilter
    ordering = ["-created_at"]
    ordering_fields = ["created_at"]

    def get_permissions(self):
        if self.action in ["update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated(), IsOwnerOrReadOnly()]
        return [permissions.IsAuthenticated()]

    def list(self, request, *args, **kwargs):
        errors = {}
        if not request.query_params.get("venue"):
            errors["venue"] = ["This query parameter is required."]
        if not (request.query_params.get("location_id") or "").strip():
            errors["location_id"] = ["This query parameter is required."]
        if errors:
            raise ValidationError(errors)
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        input_serializer = LocationMessageCreateSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        data = input_serializer.validated_data

        location_id = data["location_id"].strip()
        if not location_id:
            raise ValidationError({"location_id": ["This field may not be blank."]})

        venue = get_object_or_404(Venue.objects, pk=data["venue"])
        location_name = data.get("location_name", "").strip()

        conversation = self._get_or_create_conversation(
            venue, location_id, location_name
        )
        message = LocationMessage.objects.create(
            conversation=conversation, user=request.user, content=data["content"]
        )

        output = self.get_serializer(message)
        broadcast_location_message(venue.id, location_id, output.data)
        return Response(output.data, status=status.HTTP_201_CREATED)

    def _get_or_create_conversation(self, venue, location_id, location_name):
        conversation, created = LocationConversation.objects.get_or_create(
            venue=venue,
            location_id=location_id,
            defaults={"location_name": location_name or "Location"},
        )
        if not created and location_name and not conversation.location_name:
            conversation.location_name = location_name
            conversation.save(update_fields=["location_name", "updated_at"])
        return conversation
