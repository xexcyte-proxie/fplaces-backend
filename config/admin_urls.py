from django.urls import path
from rest_framework.routers import DefaultRouter

from forum.views.admin import AdminPostViewSet
from users.views.admin import AdminStatsView, AdminUserViewSet
from notifications.views.admin import AdminNotificationViewSet

app_name = "admin_api"

router = DefaultRouter()
router.register("users", AdminUserViewSet, basename="user")
router.register("posts", AdminPostViewSet, basename="post")
router.register("notifications", AdminNotificationViewSet, basename="notification")

urlpatterns = [
    path("stats/", AdminStatsView.as_view(), name="stats"),
] + router.urls

