from django.db import transaction
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.realtime import broadcast, venue_group
from forum.models import Post, PostFlag
from forum.serializers.admin import AdminPostSerializer

_TAGS = ["Admin"]


@extend_schema_view(
    list=extend_schema(tags=_TAGS, summary="List all posts in the system (including hidden/archived)"),
    retrieve=extend_schema(tags=_TAGS, summary="Retrieve details of a single post"),
    create=extend_schema(tags=_TAGS, summary="Create a new post manually"),
    update=extend_schema(tags=_TAGS, summary="Replace post details"),
    partial_update=extend_schema(tags=_TAGS, summary="Update post details partially"),
    destroy=extend_schema(tags=_TAGS, summary="Soft-delete/archive a post"),
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
        description="Returns posts that have been flagged one or more times, sorted by flag count descending.",
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
        description="Sets status='hidden' and broadcasts a post_hidden event so clients remove it from live feeds.",
        responses={200: AdminPostSerializer},
    )
    @action(detail=True, methods=["post"])
    def hide(self, request, pk=None):
        post = self.get_object()
        post.status = Post.STATUS_HIDDEN
        post.save(update_fields=["status", "updated_at"])
        broadcast(venue_group(post.venue_id), "post_hidden", {"post_id": post.id})
        return Response(self.get_serializer(post).data)

    @extend_schema(
        tags=_TAGS,
        summary="Un-hide a post (moderation)",
        description="Sets status='visible' so the post reappears in live feeds.",
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
        description="Resets the flags_count to 0 and archives all active PostFlag records associated with this post.",
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
        description="Resets is_archived=False on a previously soft-deleted post.",
        responses={200: AdminPostSerializer},
    )
    @action(detail=True, methods=["post"])
    def restore(self, request, pk=None):
        post = self.get_object()
        post.restore()
        return Response(self.get_serializer(post).data)
