from django.contrib.auth import get_user_model
from django.db import models
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from forum.models import Category, Comment, Post, Venue
from users.serializers.admin import AdminStatsSerializer, AdminUserSerializer

User = get_user_model()
_TAGS = ["Admin"]


@extend_schema_view(
    get=extend_schema(
        tags=_TAGS,
        summary="Get system-wide dashboard stats",
        description=(
            "Aggregate counts for the admin dashboard: total/verified user counts, "
            "total posts/comments, how many posts currently have at least one flag "
            "(see `GET /api/admin/posts/flagged/` to review them), how many venues are "
            "active, plus a per-category and per-venue breakdown of post counts. "
            "Counts include archived/soft-deleted rows (uses `all_objects`), since "
            "this is an internal operational view, not a public-facing feed."
        ),
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

        categories_data = Category.all_objects.annotate(
            post_count=models.Count("posts")
        ).values("name", "post_count")
        posts_by_category = [
            {"category_name": x["name"], "post_count": x["post_count"]}
            for x in categories_data
        ]

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
    list=extend_schema(
        tags=_TAGS,
        summary="List all users (including archived/unverified)",
        description="Unlike `users.objects` (which excludes archived users), this "
        "queries `User.all_objects` so moderators can see the complete picture, "
        "including unverified signups and previously archived accounts.",
    ),
    retrieve=extend_schema(tags=_TAGS, summary="Retrieve a single user's full admin details"),
    create=extend_schema(
        tags=_TAGS,
        summary="Create a user manually",
        description="Creates a user with no usable password (`set_unusable_password()`) "
        "since this endpoint doesn't accept one — the account holder sets their own "
        "password via `POST /api/users/password-reset/` once notified. Mainly intended "
        "for seeding staff/admin accounts outside of self-service registration.",
    ),
    update=extend_schema(tags=_TAGS, summary="Replace a user's admin-editable fields"),
    partial_update=extend_schema(tags=_TAGS, summary="Update a user's admin-editable fields"),
    destroy=extend_schema(
        tags=_TAGS,
        summary="Archive a user (soft delete)",
        description="Equivalent to `POST /{id}/archive/` — sets `is_archived=True` "
        "rather than permanently deleting the row, consistent with every other "
        "resource in this API. Use `POST /{id}/restore/` to undo.",
    ),
)
class AdminUserViewSet(viewsets.ModelViewSet):
    queryset = User.all_objects.all().order_by("-created_at")
    serializer_class = AdminUserSerializer
    permission_classes = [permissions.IsAdminUser]

    def perform_create(self, serializer):
        user = serializer.save()
        user.set_unusable_password()
        user.save(update_fields=["password"])

    def perform_destroy(self, instance):
        instance.archive()

    @extend_schema(
        tags=_TAGS,
        summary="Archive a user (soft delete)",
        description="Sets `is_archived=True` on the user so they can no longer log in "
        "(`UserManager.get_queryset` excludes archived users) and disappear from "
        "non-admin listings. Their posts/comments are untouched and remain visible.",
        request=None,
        responses={200: AdminUserSerializer},
    )
    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        user = self.get_object()
        user.archive()
        return Response(self.get_serializer(user).data)

    @extend_schema(
        tags=_TAGS,
        summary="Restore an archived user",
        description="Reverses `archive`, setting `is_archived=False` so the user can "
        "log in again and reappears in non-admin listings.",
        request=None,
        responses={200: AdminUserSerializer},
    )
    @action(detail=True, methods=["post"])
    def restore(self, request, pk=None):
        user = self.get_object()
        user.restore()
        return Response(self.get_serializer(user).data)

    @extend_schema(
        tags=_TAGS,
        summary="Toggle a user's staff status",
        description="Flips `is_staff` to its opposite value, granting or revoking "
        "Django admin + this Admin API's access in one call. There's no separate "
        "grant/revoke endpoint — call this again to toggle back.",
        request=None,
        responses={200: AdminUserSerializer},
    )
    @action(detail=True, methods=["post"], url_path="toggle-staff")
    def toggle_staff(self, request, pk=None):
        user = self.get_object()
        user.is_staff = not user.is_staff
        user.save(update_fields=["is_staff", "updated_at"])
        return Response(self.get_serializer(user).data)
