
import json
from unittest.mock import Mock

import pytest

from app.services.chat_memory import ChatMemory


@pytest.fixture
def memory():
    chat_memory = ChatMemory()

    redis_mock = Mock()
    pipeline_mock = Mock()

    # Make the pipeline usable as a context manager.
    pipeline_mock.__enter__ = Mock(
        return_value=pipeline_mock
    )
    pipeline_mock.__exit__ = Mock(
        return_value=False
    )

    redis_mock.pipeline.return_value = pipeline_mock

    chat_memory.redis = redis_mock

    return chat_memory, redis_mock, pipeline_mock


def test_get_history_returns_messages(memory):
    chat_memory, redis_mock, pipeline = memory

    messages = [
        json.dumps({
            "role": "user",
            "content": "Hello"
        }),
        json.dumps({
            "role": "assistant",
            "content": "Hi there"
        })
    ]

    redis_mock.lrange.return_value = messages

    result = chat_memory.get_history(
        session_id="test-session"
    )

    assert result == [
        {
            "role": "user",
            "content": "Hello"
        },
        {
            "role": "assistant",
            "content": "Hi there"
        }
    ]

    redis_mock.lrange.assert_called_once_with(
        "chat:test-session",
        -10,
        -1
    )


def test_get_history_uses_custom_limit(memory):
    chat_memory, redis_mock, pipeline = memory

    redis_mock.lrange.return_value = []

    chat_memory.get_history(
        session_id="test-session",
        limit=5
    )

    redis_mock.lrange.assert_called_once_with(
        "chat:test-session",
        -5,
        -1
    )


@pytest.mark.parametrize(
    "limit",
    [0, -1, 21, 100]
)
def test_invalid_history_limit(memory, limit):
    chat_memory, redis_mock, pipeline = memory

    with pytest.raises(
        ValueError,
        match="History limit must be between 1 and 20"
    ):
        chat_memory.get_history(
            session_id="test-session",
            limit=limit
        )

    redis_mock.lrange.assert_not_called()


def test_add_message_stores_message(memory):
    chat_memory, redis_mock, pipeline = memory

    chat_memory.add_message(
        session_id="test-session",
        role="user",
        content="Hello"
    )

    stored_message = json.dumps({
        "role": "user",
        "content": "Hello"
    })

    redis_mock.pipeline.assert_called_once_with(
        transaction=True
    )

    pipeline.rpush.assert_called_once_with(
        "chat:test-session",
        stored_message
    )

    pipeline.ltrim.assert_called_once_with(
        "chat:test-session",
        -20,
        -1
    )

    pipeline.expire.assert_called_once_with(
        "chat:test-session",
        86400
    )

    pipeline.execute.assert_called_once()


def test_add_message_rejects_invalid_role(memory):
    chat_memory, redis_mock, pipeline = memory

    with pytest.raises(
        ValueError,
        match="Invalid chat message role"
    ):
        chat_memory.add_message(
            session_id="test-session",
            role="system",
            content="Hello"
        )

    redis_mock.pipeline.assert_not_called()


def test_add_message_rejects_empty_content(memory):
    chat_memory, redis_mock, pipeline = memory

    with pytest.raises(
        ValueError,
        match="Message content cannot be empty"
    ):
        chat_memory.add_message(
            session_id="test-session",
            role="user",
            content="   "
        )

    redis_mock.pipeline.assert_not_called()


def test_add_exchange_stores_both_messages_atomically(memory):
    chat_memory, redis_mock, pipeline = memory

    chat_memory.add_exchange(
        session_id="test-session",
        question="What is Python?",
        answer="Python is a programming language."
    )

    redis_mock.pipeline.assert_called_once_with(
        transaction=True
    )

    # Both messages are added in one RPUSH operation.
    pipeline.rpush.assert_called_once()

    args = pipeline.rpush.call_args.args

    assert args[0] == "chat:test-session"

    user_message = json.loads(args[1])
    assistant_message = json.loads(args[2])

    assert user_message == {
        "role": "user",
        "content": "What is Python?"
    }

    assert assistant_message == {
        "role": "assistant",
        "content": "Python is a programming language."
    }

    pipeline.ltrim.assert_called_once_with(
        "chat:test-session",
        -20,
        -1
    )

    pipeline.expire.assert_called_once_with(
        "chat:test-session",
        86400
    )

    pipeline.execute.assert_called_once()


@pytest.mark.parametrize(
    ("question", "answer"),
    [
        ("", "Answer"),
        ("Question", ""),
        ("   ", "Answer"),
        ("Question", "   ")
    ]
)
def test_add_exchange_rejects_empty_messages(
    memory,
    question,
    answer
):
    chat_memory, redis_mock, pipeline = memory

    with pytest.raises(
        ValueError,
        match="Question and answer cannot be empty"
    ):
        chat_memory.add_exchange(
            session_id="test-session",
            question=question,
            answer=answer
        )

    redis_mock.pipeline.assert_not_called()


def test_add_exchange_executes_transaction_once(memory):
    chat_memory, redis_mock, pipeline = memory

    chat_memory.add_exchange(
        session_id="test-session",
        question="Question",
        answer="Answer"
    )

    pipeline.execute.assert_called_once()
    pipeline.__exit__.assert_called_once()
