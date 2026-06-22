from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from core.views import root_view

admin.site.site_header = "fPlaces Admin Dashboard"
admin.site.site_title = "fPlaces Admin Portal"
admin.site.index_title = "fPlaces System Administration"

urlpatterns = [
    path("favicon.ico", lambda _: HttpResponse(status=204)),
    path("", root_view, name="root"),
    path("admin/", admin.site.urls),
    path("api/admin/", include("config.admin_urls")),
    path("api/users/", include("users.urls")),
    path("api/forum/", include("forum.urls")),
    path("api/notifications/", include("notifications.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

