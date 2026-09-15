import hashlib

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def broadcast(group_name, event_type, payload):
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    async_to_sync(channel_layer.group_send)(
        group_name,
        {"type": "broadcast.message", "event": event_type, "payload": payload},
    )


def venue_group(venue_id):
    return f"venue_{venue_id}"


def location_group(venue_id, location_id):
    # location_id is an opaque, client-supplied string (e.g. a Mappedin place id) that may
    # contain characters the channel layer's group-name charset (and length limit) forbid,
    # so it's hashed into a fixed-length, always-valid group name rather than used verbatim.
    digest = hashlib.sha256(str(location_id).encode()).hexdigest()[:32]
    return f"location_{venue_id}_{digest}"


def broadcast_location_message(venue_id, location_id, message):
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    async_to_sync(channel_layer.group_send)(
        location_group(venue_id, location_id),
        {"type": "location.message", "message": message},
    )


def user_group(user_id):
    return f"user_{user_id}"
