from django.db import transaction
from django.db.models import F
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from core.permissions import IsOwnerOrReadOnly
from core.realtime import broadcast, venue_group
from core.viewsets import BaseViewSet
from forum.filters import PostFilter
from forum.models import Post, PostFlag, PostVote
from forum.serializers import PostFlagRequestSerializer, PostSerializer

_TAGS = ["Posts"]


@extend_schema_view(
    list=extend_schema(
        tags=_TAGS,
        summary="List posts in the live feed",
        description="Requires authentication, since the feed is venue-scoped to logged-in "
        "fans. By default excludes posts a moderator has hidden (`status=hidden`) unless "
        "the requester is staff. The same `new_post`/`new_comment`/`upvote_update`/"
        "`section_heat_update`/`post_hidden` events are pushed live on "
        "`ws/venues/<venue_id>/`, so clients typically paginate this endpoint for the "
        "initial load and then rely on the socket for live updates.",
        parameters=[
            OpenApiParameter("venue", int, description="Filter to posts in this venue."),
            OpenApiParameter("category", int, description="Filter to posts in this category."),
            OpenApiParameter("section", int, description="Filter to posts in this section."),
            OpenApiParameter(
                "latest", bool, description="If true, force ordering by newest first."
            ),
        ],
    ),
    retrieve=extend_schema(tags=_TAGS, summary="Retrieve a post"),
    create=extend_schema(
        tags=_TAGS,
        summary="Create a post",
        description="`content` is capped at 140 characters. `user` is set from the "
        "authenticated requester and can't be overridden. Creating a post broadcasts a "
        "`new_post` event to the venue's WebSocket room, and a `section_heat_update` "
        "event if `section` is set.",
    ),
    update=extend_schema(
        tags=_TAGS, summary="Replace a post", description="Only the post's own author or staff may edit it."
    ),
    partial_update=extend_schema(
        tags=_TAGS,
        summary="Update a post",
        description="Only the post's own author or staff may edit it.",
    ),
    destroy=extend_schema(
        tags=_TAGS,
        summary="Archive a post (soft delete)",
        description="Only the post's own author or staff may delete it. This sets "
        "`is_archived=True`; the row and its comments/votes/flags are preserved.",
    ),
    restore=extend_schema(tags=_TAGS, summary="Restore an archived post"),
)
class PostViewSet(BaseViewSet):
    queryset = Post.objects.select_related("user", "venue", "section", "category")
    serializer_class = PostSerializer
    filterset_class = PostFilter
    ordering = ["-created_at"]
    ordering_fields = ["created_at", "upvotes_count"]

    def get_permissions(self):
        if self.action in ["update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated(), IsOwnerOrReadOnly()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = super().get_queryset()
        if not (self.request.user.is_authenticated and self.request.user.is_staff):
            queryset = queryset.exclude(status=Post.STATUS_HIDDEN)
        return queryset

    def perform_create(self, serializer):
        post = serializer.save(user=self.request.user)

        broadcast(
            venue_group(post.venue_id),
            "new_post",
            self.get_serializer(post).data,
        )

        if post.section_id:
            heat = Post.objects.filter(
                section_id=post.section_id, status=Post.STATUS_VISIBLE
            ).count()
            broadcast(
                venue_group(post.venue_id),
                "section_heat_update",
                {"section_id": post.section_id, "post_count": heat},
            )

    @extend_schema(
        tags=_TAGS,
        summary="Toggle my upvote",
        description="Idempotent toggle: upvotes the post if the requester hasn't "
        "upvoted it yet, or removes their upvote if they have. Enforced one-vote-per-user "
        "via a `PostVote` row (soft-archived rather than deleted when toggled off). "
        "Broadcasts an `upvote_update` event to the venue's WebSocket room either way.",
        request=None,
        responses={200: PostSerializer},
    )
    @action(detail=True, methods=["post"])
    def upvote(self, request, pk=None):
        post = self.get_object()

        with transaction.atomic():
            vote, created = PostVote.all_objects.get_or_create(post=post, user=request.user)
            if created:
                upvoted = True
                Post.objects.filter(pk=post.pk).update(upvotes_count=F("upvotes_count") + 1)
            elif vote.is_archived:
                vote.restore()
                upvoted = True
                Post.objects.filter(pk=post.pk).update(upvotes_count=F("upvotes_count") + 1)
            else:
                vote.archive()
                upvoted = False
                Post.objects.filter(pk=post.pk).update(upvotes_count=F("upvotes_count") - 1)

        post.refresh_from_db()
        broadcast(
            venue_group(post.venue_id),
            "upvote_update",
            {"post_id": post.id, "upvotes_count": post.upvotes_count, "upvoted": upvoted},
        )
        return Response(self.get_serializer(post).data)

    @extend_schema(
        tags=_TAGS,
        summary="Flag a post for moderation",
        description="Idempotent: flagging the same post twice doesn't double-count "
        "`flags_count`. One `PostFlag` row per `(post, user)`; flagging again after the "
        "flag was cleared by a moderator re-activates it. Doesn't broadcast over "
        "WebSocket — flags are moderator-facing, not part of the public feed.",
        request=PostFlagRequestSerializer,
        responses={200: PostSerializer},
    )
    @action(detail=True, methods=["post"])
    def flag(self, request, pk=None):
        post = self.get_object()
        flag_request = PostFlagRequestSerializer(data=request.data)
        flag_request.is_valid(raise_exception=True)
        reason = flag_request.validated_data.get("reason", "")

        with transaction.atomic():
            flag, created = PostFlag.all_objects.get_or_create(
                post=post, user=request.user, defaults={"reason": reason}
            )
            if created:
                Post.objects.filter(pk=post.pk).update(flags_count=F("flags_count") + 1)
            elif flag.is_archived:
                flag.restore()
                Post.objects.filter(pk=post.pk).update(flags_count=F("flags_count") + 1)

        post.refresh_from_db()
        return Response(self.get_serializer(post).data)

