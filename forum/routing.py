from django.urls import re_path

from forum.consumers import LocationConsumer, VenueConsumer

websocket_urlpatterns = [
    re_path(r"^ws/venues/(?P<venue_id>\d+)/$", VenueConsumer.as_asgi()),
    re_path(
        r"^ws/venues/(?P<venue_id>\d+)/locations/(?P<location_id>[^/]+)/$",
        LocationConsumer.as_asgi(),
    ),
]
