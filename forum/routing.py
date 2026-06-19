from django.urls import re_path

from forum.consumers import VenueConsumer

websocket_urlpatterns = [
    re_path(r"^ws/venues/(?P<venue_id>\d+)/$", VenueConsumer.as_asgi()),
]
