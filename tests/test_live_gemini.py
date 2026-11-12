
import os

import pytest

from app.services.llm_service import llm_service


@pytest.mark.skipif(
    os.getenv("RUN_LIVE_GEMINI") != "1",
    reason="Set RUN_LIVE_GEMINI=1 to call the real Gemini API."
)
def test_live_gemini_generation():
    response = llm_service.generate_text(
        "Reply with exactly this text: GEMINI_CONNECTION_OK"
    )

    assert response
    assert isinstance(response, str)
    assert "GEMINI_CONNECTION_OK" in response


@pytest.mark.skipif(
    os.getenv("RUN_LIVE_GEMINI") != "1",
    reason="Set RUN_LIVE_GEMINI=1 to call the real Gemini API."
)
def test_live_gemini_query_rewriting():
    history = [
        {
            "role": "user",
            "content": "Tell me about Python."
        },
        {
            "role": "assistant",
            "content": "Python is a programming language."
        }
    ]

    rewritten = llm_service.rewrite_question(
        question="What are its main features?",
        conversation_history=history
    )

    assert rewritten.strip()
    assert "Python" in rewritten


@pytest.mark.skipif(
    os.getenv("RUN_LIVE_GEMINI") != "1",
    reason="Set RUN_LIVE_GEMINI=1 to call the real Gemini API."
)
def test_live_gemini_grounded_answer():
    chunks = [
        {
            "filename": "python.txt",
            "chunk_index": 0,
            "text": (
                "Python supports object-oriented programming "
                "and functional programming."
            )
        }
    ]

    answer = llm_service.generate_answer(
        question="What programming paradigms does Python support?",
        retrieved_chunks=chunks,
        conversation_history=[]
    )

    assert answer.strip()
    assert "object-oriented" in answer.lower()
