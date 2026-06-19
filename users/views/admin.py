from django.contrib.auth import get_user_model
from django.db import models
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from forum.models import Comment, Post, Venue
from users.serializers.admin import AdminStatsSerializer, AdminUserSerializer

User = get_user_model()
_TAGS = ["Admin"]


@extend_schema_view(
    get=extend_schema(
        tags=_TAGS,
        summary="Get system-wide dashboard stats",
        description="Returns counts and category/venue breakdowns of users, posts, and comments.",
        responses={200: AdminStatsSerializer},
    )
)
class AdminStatsView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        total_users = User.all_objects.count()
        verified_users = User.all_objects.filter(is_email_verified=True).count()
        total_posts = Post.all_objects.count()
        total_comments = Comment.all_objects.count()
        flagged_posts_count = Post.all_objects.filter(flags_count__gt=0).count()
        active_venues_count = Venue.all_objects.filter(is_archived=False).count()

        # Posts by category breakdown
        from forum.models import Category
        categories_data = Category.all_objects.annotate(
            post_count=models.Count("posts")
        ).values("name", "post_count")
        posts_by_category = [
            {"category_name": x["name"], "post_count": x["post_count"]}
            for x in categories_data
        ]

        # Posts by venue breakdown
        venues_data = Venue.all_objects.annotate(
            post_count=models.Count("posts")
        ).values("name", "post_count")
        posts_by_venue = [
            {"venue_name": x["name"], "post_count": x["post_count"]}
            for x in venues_data
        ]

        data = {
            "total_users": total_users,
            "verified_users": verified_users,
            "total_posts": total_posts,
            "total_comments": total_comments,
            "flagged_posts_count": flagged_posts_count,
            "active_venues_count": active_venues_count,
            "posts_by_category": posts_by_category,
            "posts_by_venue": posts_by_venue,
        }
        serializer = AdminStatsSerializer(data)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(tags=_TAGS, summary="List all users in the system (including archived/unverified)"),
    retrieve=extend_schema(tags=_TAGS, summary="Retrieve details of a single user"),
    create=extend_schema(tags=_TAGS, summary="Create a new user manually"),
    update=extend_schema(tags=_TAGS, summary="Replace user details"),
    partial_update=extend_schema(tags=_TAGS, summary="Update user details partially"),
    destroy=extend_schema(tags=_TAGS, summary="Delete a user (hard delete)"),
)
class AdminUserViewSet(viewsets.ModelViewSet):
    queryset = User.all_objects.all().order_index = ["-created_at"]
    queryset = User.all_objects.all().order_by("-created_at")
    serializer_class = AdminUserSerializer
    permission_classes = [permissions.IsAdminUser]

    @extend_schema(
        tags=_TAGS,
        summary="Soft-delete/archive a user",
        description="Sets is_archived=True on the user record so they cannot log in or appear in active listings.",
        responses={200: AdminUserSerializer},
    )
    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        user = self.get_object()
        user.archive()
        return Response(self.get_serializer(user).data)

    @extend_schema(
        tags=_TAGS,
        summary="Restore a soft-deleted/archived user",
        description="Resets is_archived=False on the user record.",
        responses={200: AdminUserSerializer},
    )
    @action(detail=True, methods=["post"])
    def restore(self, request, pk=None):
        user = self.get_object()
        user.restore()
        return Response(self.get_serializer(user).data)

    @extend_schema(
        tags=_TAGS,
        summary="Toggle user staff permissions status",
        description="Toggles the is_staff boolean field on the user.",
        responses={200: AdminUserSerializer},
    )
    @action(detail=True, methods=["post"], url_path="toggle-staff")
    def toggle_staff(self, request, pk=None):
        user = self.get_object()
        user.is_staff = not user.is_staff
        user.save(update_fields=["is_staff", "updated_at"])
        return Response(self.get_serializer(user).data)
