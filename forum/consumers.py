from core.consumers import BroadcastConsumer
from core.realtime import venue_group


class VenueConsumer(BroadcastConsumer):
    async def get_group_name(self):
        venue_id = self.scope["url_route"]["kwargs"]["venue_id"]
        return venue_group(venue_id)
