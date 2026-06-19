from django.contrib import admin

from forum.models import Category, Comment, Post, PostFlag, PostVote, Section, Venue


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "order", "is_active", "is_archived", "created_at"]
    list_filter = ["is_active", "is_archived"]
    search_fields = ["name", "description"]
    ordering = ["order", "name"]
    readonly_fields = ["created_at", "updated_at"]
    prepopulated_fields = {"slug": ("name",)}

    def get_queryset(self, request):
        return Category.all_objects.all()


class SectionInline(admin.TabularInline):
    model = Section
    extra = 0
    fields = ["name", "code", "is_active", "is_archived"]


@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ["name", "location", "is_archived", "created_at"]
    list_filter = ["is_archived"]
    search_fields = ["name", "location"]
    readonly_fields = ["created_at", "updated_at"]
    inlines = [SectionInline]

    def get_queryset(self, request):
        return Venue.all_objects.all()


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ["venue", "name", "code", "is_active", "is_archived", "created_at"]
    list_filter = ["venue", "is_active", "is_archived"]
    search_fields = ["name", "code"]
    readonly_fields = ["created_at", "updated_at"]

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
