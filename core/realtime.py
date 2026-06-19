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


def user_group(user_id):
    return f"user_{user_id}"
