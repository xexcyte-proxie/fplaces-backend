from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import path

from forum.models import (
    Category,
    Comment,
    Floor,
    Interest,
    LocationConversation,
    LocationMessage,
    Post,
    PostFlag,
    PostVote,
    Section,
    Venue,
)
from forum.services.mappedin_sync import sync_venue_from_mappedin


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "slug",
        "icon_url",
        "order",
        "is_active",
        "is_archived",
        "created_at",
    ]
    list_filter = ["is_active", "is_archived"]
    search_fields = ["name", "description", "icon_url"]
    ordering = ["order", "name"]
    readonly_fields = ["created_at", "updated_at"]
    prepopulated_fields = {"slug": ("name",)}

    def get_queryset(self, request):
        return Category.all_objects.all()


@admin.register(Interest)
class InterestAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "order", "is_active", "is_archived", "created_at"]
    list_filter = ["is_active", "is_archived"]
    search_fields = ["name"]
    ordering = ["order", "name"]
    readonly_fields = ["created_at", "updated_at"]
    prepopulated_fields = {"slug": ("name",)}

    def get_queryset(self, request):
        return Interest.all_objects.all()


class SectionInline(admin.TabularInline):
    model = Section
    extra = 0
    fields = ["name", "code", "floor", "is_active", "is_archived"]


class FloorInline(admin.TabularInline):
    model = Floor
    extra = 0
    fields = ["name", "mappedin_floor_id", "elevation", "order", "is_archived"]
    readonly_fields = ["mappedin_floor_id"]


@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "location",
        "mappedin_map_id",
        "latitude",
        "longitude",
        "is_archived",
        "created_at",
    ]
    list_filter = ["is_archived"]
    search_fields = ["name", "location"]
    readonly_fields = ["raw_json", "created_at", "updated_at"]
    inlines = [FloorInline, SectionInline]
    change_form_template = "admin/forum/venue/change_form.html"

    def get_queryset(self, request):
        return Venue.all_objects.all()

    def get_urls(self):
        custom_urls = [
            path(
                "<int:venue_id>/sync-mappedin/",
                self.admin_site.admin_view(self.sync_mappedin_view),
                name="forum_venue_sync_mappedin",
            ),
        ]
        return custom_urls + super().get_urls()

    def sync_mappedin_view(self, request, venue_id):
        venue = self.get_object(request, venue_id)
        if venue is None:
            self.message_user(request, "Venue not found.", level=messages.ERROR)
            return redirect("admin:forum_venue_changelist")

        if not venue.mappedin_map_id:
            self.message_user(
                request,
                "This venue has no mappedin_map_id set — nothing to sync.",
                level=messages.WARNING,
            )
            return redirect("admin:forum_venue_change", venue_id)

        try:
            result = sync_venue_from_mappedin(venue)
        except Exception as exc:
            self.message_user(
                request, f"Mappedin sync failed: {exc}", level=messages.ERROR
            )
            return redirect("admin:forum_venue_change", venue_id)

        if not result["venue_found"]:
            self.message_user(
                request,
                f"mappedin_map_id {venue.mappedin_map_id!r} wasn't found in Mappedin's venue "
                f"list, so latitude/longitude weren't updated. Synced {result['floors_count']} "
                f"floor(s) and {result['sections_count']} section(s) from the map export anyway.",
                level=messages.WARNING,
            )
        else:
            self.message_user(
                request,
                f"Synced {result['floors_count']} floor(s) and {result['sections_count']} "
                "section(s) from Mappedin.",
                level=messages.SUCCESS,
            )
        return redirect("admin:forum_venue_change", venue_id)


@admin.register(Floor)
class FloorAdmin(admin.ModelAdmin):
    list_display = [
        "venue",
        "name",
        "mappedin_floor_id",
        "elevation",
        "order",
        "is_archived",
        "created_at",
    ]
    list_filter = ["venue", "is_archived"]
    search_fields = ["name", "mappedin_floor_id"]
    readonly_fields = ["mappedin_floor_id", "raw_json", "created_at", "updated_at"]

    def get_queryset(self, request):
        return Floor.all_objects.all()


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = [
        "venue",
        "floor",
        "name",
        "code",
        "mappedin_location_id",
        "is_active",
        "is_archived",
        "created_at",
    ]
    list_filter = ["venue", "floor", "is_active", "is_archived"]
    search_fields = ["name", "code", "mappedin_location_id"]
    readonly_fields = ["mappedin_location_id", "raw_json", "created_at", "updated_at"]

    def get_queryset(self, request):
        return Section.all_objects.all()


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "venue",
        "section",
        "category",
        "status",
        "upvotes_count",
        "flags_count",
        "created_at",
    ]
    list_filter = ["status", "venue", "category", "is_archived"]
    search_fields = ["content", "user__email"]
    readonly_fields = ["upvotes_count", "flags_count", "created_at", "updated_at"]

    def get_queryset(self, request):
        return Post.all_objects.all()


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ["id", "post", "user", "created_at"]
    search_fields = ["content", "user__email"]
    readonly_fields = ["created_at", "updated_at"]

    def get_queryset(self, request):
        return Comment.all_objects.all()


@admin.register(LocationConversation)
class LocationConversationAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "venue",
        "location_id",
        "location_name",
        "is_archived",
        "created_at",
    ]
    list_filter = ["venue", "is_archived"]
    search_fields = ["location_id", "location_name"]
    readonly_fields = ["created_at", "updated_at"]

    def get_queryset(self, request):
        return LocationConversation.all_objects.all()


@admin.register(LocationMessage)
class LocationMessageAdmin(admin.ModelAdmin):
    list_display = ["id", "conversation", "user", "created_at"]
    list_filter = ["conversation__venue"]
    search_fields = ["content", "user__email"]
    readonly_fields = ["created_at", "updated_at"]

    def get_queryset(self, request):
        return LocationMessage.all_objects.all()


@admin.register(PostVote)
class PostVoteAdmin(admin.ModelAdmin):
    list_display = ["post", "user", "is_archived", "created_at"]
    list_filter = ["is_archived"]

    def get_queryset(self, request):
        return PostVote.all_objects.all()


@admin.register(PostFlag)
class PostFlagAdmin(admin.ModelAdmin):
    list_display = ["post", "user", "reason", "is_archived", "created_at"]
    list_filter = ["is_archived"]

    def get_queryset(self, request):
        return PostFlag.all_objects.all()
