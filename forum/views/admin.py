from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.realtime import broadcast, venue_group
from forum.models import Post, PostFlag
from forum.serializers.admin import AdminPostSerializer
from forum.utils import broadcast_venue_heatmap

_TAGS = ["Admin"]


@extend_schema_view(
    list=extend_schema(
        tags=_TAGS,
        summary="List all posts (including hidden/archived)",
        description="Queries `Post.all_objects`, unlike the public `PostViewSet` "
        "(which excludes archived posts and hides `status=hidden` posts from "
        "non-staff). Use this for full moderation visibility, or "
        "`GET /flagged/` to focus specifically on posts awaiting review.",
    ),
    retrieve=extend_schema(tags=_TAGS, summary="Retrieve a single post's full admin details"),
    create=extend_schema(
        tags=_TAGS,
        summary="Create a post on a user's behalf",
        description="Unlike the public `PostViewSet.create` (which always sets "
        "`user` from the authenticated requester), `user` is a writable field here "
        "so admins can create posts attributed to any account, e.g. for seeding "
        "demo content.",
    ),
    update=extend_schema(tags=_TAGS, summary="Replace a post's admin-editable fields"),
    partial_update=extend_schema(tags=_TAGS, summary="Update a post's admin-editable fields"),
    destroy=extend_schema(
        tags=_TAGS,
        summary="Archive a post (soft delete)",
        description="Sets `is_archived=True` rather than permanently deleting the "
        "row. Use `POST /{id}/restore/` to undo.",
    ),
)
class AdminPostViewSet(viewsets.ModelViewSet):
    queryset = Post.all_objects.all().order_by("-created_at")
    serializer_class = AdminPostSerializer
    permission_classes = [permissions.IsAdminUser]

    def perform_destroy(self, instance):
        instance.archive()

    @extend_schema(
        tags=_TAGS,
        summary="List posts flagged for moderation",
        description="Returns posts with `flags_count > 0`, sorted by flag count "
        "descending (most-flagged first), then newest first. This is the "
        "moderation queue — review each post and either `POST /{id}/clear-flags/` "
        "once resolved, or `POST /{id}/hide/` to remove it from public feeds.",
        responses={200: AdminPostSerializer(many=True)},
    )
    @action(detail=False, methods=["get"])
    def flagged(self, request):
        queryset = self.get_queryset().filter(flags_count__gt=0).order_by("-flags_count", "-created_at")
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=_TAGS,
        summary="Hide a post (moderation)",
        description="Sets `status=hidden`, removing the post from non-staff feeds "
        "(it's a moderation state, not a soft-delete — the row stays active). "
        "Broadcasts a `post_hidden` event to the venue's WebSocket room so clients "
        "currently viewing the feed remove it immediately. Equivalent to the "
        "public `PostViewSet`'s own `hide` action, exposed here for the admin "
        "dashboard's moderation queue workflow.",
        request=None,
        responses={200: AdminPostSerializer},
    )
    @action(detail=True, methods=["post"])
    def hide(self, request, pk=None):
        post = self.get_object()
        post.status = Post.STATUS_HIDDEN
        post.save(update_fields=["status", "updated_at"])
        broadcast(venue_group(post.venue_id), "post_hidden", {"post_id": post.id})
        
        if post.section_id:
            broadcast_venue_heatmap(post.venue_id)
            
        return Response(self.get_serializer(post).data)

    @extend_schema(
        tags=_TAGS,
        summary="Un-hide a post (moderation)",
        description="Reverses `hide`, setting `status=visible` so the post "
        "reappears in non-staff feeds.",
        request=None,
        responses={200: AdminPostSerializer},
    )
    @action(detail=True, methods=["post"])
    def show(self, request, pk=None):
        post = self.get_object()
        post.status = Post.STATUS_VISIBLE
        post.save(update_fields=["status", "updated_at"])
        return Response(self.get_serializer(post).data)

    @extend_schema(
        tags=_TAGS,
        summary="Clear all flags on a post",
        description="Resets `flags_count` to `0` and soft-archives every active "
        "`PostFlag` row for this post (preserving them for audit history rather "
        "than deleting). Use once a moderator has reviewed a flagged post and "
        "decided it doesn't need hiding.",
        request=None,
        responses={200: AdminPostSerializer},
    )
    @action(detail=True, methods=["post"], url_path="clear-flags")
    def clear_flags(self, request, pk=None):
        post = self.get_object()
        with transaction.atomic():
            post.flags_count = 0
            post.save(update_fields=["flags_count", "updated_at"])
            PostFlag.all_objects.filter(post=post).update(is_archived=True)
        return Response(self.get_serializer(post).data)

    @extend_schema(
        tags=_TAGS,
        summary="Restore an archived post",
        description="Reverses soft-delete, setting `is_archived=False` so the post "
        "reappears in normal queries.",
        request=None,
        responses={200: AdminPostSerializer},
    )
    @action(detail=True, methods=["post"])
    def restore(self, request, pk=None):
        post = self.get_object()
        post.restore()
        return Response(self.get_serializer(post).data)
