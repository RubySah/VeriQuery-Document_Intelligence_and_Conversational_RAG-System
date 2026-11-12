
import json

from redis import Redis

from app.core.config import settings


class ChatMemory:
    def __init__(self):
        self.redis = Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            health_check_interval=30
        )

    def get_history(
        self,
        session_id: str,
        limit: int = 10
    ) -> list[dict]:
        if not 1 <= limit <= 20:
            raise ValueError("History limit must be between 1 and 20.")

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
        """Add a single message to conversation history."""

        if role not in {"user", "assistant"}:
            raise ValueError("Invalid chat message role.")

        if not content.strip():
            raise ValueError("Message content cannot be empty.")

        key = f"chat:{session_id}"

        message = json.dumps({
            "role": role,
            "content": content
        })

        with self.redis.pipeline(transaction=True) as pipeline:
            pipeline.rpush(key, message)
            pipeline.ltrim(key, -20, -1)
            pipeline.expire(key, 86400)
            pipeline.execute()

    def add_exchange(
        self,
        session_id: str,
        question: str,
        answer: str
    ) -> None:
        """
        Save a complete user-assistant exchange atomically.
        """

        if not question.strip() or not answer.strip():
            raise ValueError(
                "Question and answer cannot be empty."
            )

        key = f"chat:{session_id}"

        user_message = json.dumps({
            "role": "user",
            "content": question
        })

        assistant_message = json.dumps({
            "role": "assistant",
            "content": answer
        })

        with self.redis.pipeline(transaction=True) as pipeline:
            pipeline.rpush(
                key,
                user_message,
                assistant_message
            )
            pipeline.ltrim(key, -20, -1)
            pipeline.expire(key, 86400)
            pipeline.execute()


chat_memory = ChatMemory()
