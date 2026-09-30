import json

from channels.generic.websocket import AsyncWebsocketConsumer


class BroadcastConsumer(AsyncWebsocketConsumer):
    group_name = None

    async def connect(self):
        if self.scope["user"] is None or self.scope["user"].is_anonymous:
            await self.close()
            return

        self.group_name = await self.get_group_name()
        if self.group_name is None:
            await self.close()
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)

        from core.presence import presence_manager

        count = await presence_manager.add_user(self.group_name, self.scope["user"].id)

        await self.accept()

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "broadcast_message",
                "event": "presence_update",
                "payload": {"online_count": count},
            },
        )

    async def disconnect(self, close_code):
        if self.group_name:
            if self.scope["user"] and not self.scope["user"].is_anonymous:
                from core.presence import presence_manager

                count = await presence_manager.remove_user(
                    self.group_name, self.scope["user"].id
                )
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        "type": "broadcast_message",
                        "event": "presence_update",
                        "payload": {"online_count": count},
                    },
                )
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def get_group_name(self):
        raise NotImplementedError

    async def broadcast_message(self, event):
        await self.send(
            text_data=json.dumps({"event": event["event"], "payload": event["payload"]})
        )
