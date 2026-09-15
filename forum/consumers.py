import json

from core.consumers import BroadcastConsumer
from core.realtime import location_group, venue_group


class VenueConsumer(BroadcastConsumer):
    async def get_group_name(self):
        venue_id = self.scope["url_route"]["kwargs"]["venue_id"]
        return venue_group(venue_id)


class LocationConsumer(BroadcastConsumer):
    async def get_group_name(self):
        venue_id = self.scope["url_route"]["kwargs"]["venue_id"]
        location_id = self.scope["url_route"]["kwargs"]["location_id"]
        return location_group(venue_id, location_id)

    async def location_message(self, event):
        await self.send(
            text_data=json.dumps(
                {"type": "new_location_message", "message": event["message"]}
            )
        )
