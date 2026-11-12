
import json

from redis import Redis

from app.core.config import settings


class ChatMemory:
    def __init__(self):
        self.redis = Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True
        )

    def get_history(
        self,
        session_id: str,
        limit: int = 10
    ) -> list[dict]:
        key = f"chat:{session_id}"

        messages = self.redis.lrange(key, -limit, -1)

        return [
            json.loads(message)
            for message in messages
        ]

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str
    ) -> None:
        key = f"chat:{session_id}"

        message = {
            "role": role,
            "content": content
        }

        self.redis.rpush(key, json.dumps(message))
        self.redis.ltrim(key, -20, -1)

        # Automatically remove inactive conversations after 24 hours.
        self.redis.expire(key, 86400)


chat_memory = ChatMemory()
