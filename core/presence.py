from django.conf import settings
import redis.asyncio as redis


class PresenceManager:
    def __init__(self):
        self.redis = None
        if settings.REDIS_URL:
            self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
        else:
            # Fallback for local development without Redis
            self._local_presence = {}

    async def add_user(self, group_name: str, user_id: str) -> int:
        user_id = str(user_id)
        if self.redis:
            key = f"presence:{group_name}"
            await self.redis.sadd(key, user_id)
            return await self.redis.scard(key)
        else:
            if group_name not in self._local_presence:
                self._local_presence[group_name] = set()
            self._local_presence[group_name].add(user_id)
            return len(self._local_presence[group_name])

    async def remove_user(self, group_name: str, user_id: str) -> int:
        user_id = str(user_id)
        if self.redis:
            key = f"presence:{group_name}"
            await self.redis.srem(key, user_id)
            return await self.redis.scard(key)
        else:
            if group_name in self._local_presence:
                self._local_presence[group_name].discard(user_id)
                return len(self._local_presence[group_name])
            return 0

    async def get_count(self, group_name: str) -> int:
        if self.redis:
            key = f"presence:{group_name}"
            return await self.redis.scard(key)
        else:
            return len(self._local_presence.get(group_name, set()))


presence_manager = PresenceManager()
