from django.urls import re_path

from forum.consumers import SectionConsumer, VenueConsumer

websocket_urlpatterns = [
    re_path(r"^ws/venues/(?P<venue_id>\d+)/$", VenueConsumer.as_asgi()),
    re_path(r"^ws/sections/(?P<section_id>\d+)/$", SectionConsumer.as_asgi()),
]
