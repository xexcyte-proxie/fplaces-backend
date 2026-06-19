from core.consumers import BroadcastConsumer
from core.realtime import user_group


class NotificationConsumer(BroadcastConsumer):
    async def get_group_name(self):
        return user_group(self.scope["user"].id)
