from django.contrib import admin

from notifications.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["recipient", "actor", "verb", "is_read", "created_at"]
    list_filter = ["verb", "is_read"]
    search_fields = ["recipient__email", "actor__email", "message"]
    readonly_fields = ["created_at", "updated_at"]

    def get_queryset(self, request):
        return Notification.all_objects.all()
