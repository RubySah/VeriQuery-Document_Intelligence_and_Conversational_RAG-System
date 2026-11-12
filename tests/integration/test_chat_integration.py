
from uuid import uuid4

from app.services.document_service import ingest_document
from app.services import chat_service
from app.services.chat_memory import chat_memory


def test_multi_turn_conversation_with_real_services(
    db_session,
    monkeypatch
):
    # Step 1: Ingest a document into PostgreSQL and Qdrant.
    content = (
        "Python is a high-level programming language. "
        "Python supports object-oriented programming. "
        "Python also supports functional programming. "
        "Python is commonly used in data science and AI."
    )

    ingestion = ingest_document(
        db=db_session,
        filename="python_integration.txt",
        file_bytes=content.encode("utf-8"),
        strategy="fixed"
    )

    document_id = ingestion["document_id"]
    session_id = str(uuid4())

    # Step 2: Mock only the LLM generation.
    def fake_generate_answer(
        question,
        retrieved_chunks,
        conversation_history
    ):
        assert retrieved_chunks
        return "Python supports object-oriented programming."

    def fake_rewrite_question(
        question,
        conversation_history
    ):
        return "Does Python support object-oriented programming?"

    monkeypatch.setattr(
        chat_service.llm_service,
        "generate_answer",
        fake_generate_answer
    )

    monkeypatch.setattr(
        chat_service.llm_service,
        "rewrite_question",
        fake_rewrite_question
    )

    # Step 3: First user message.
    first_result = chat_service.process_chat(
        question="Tell me about Python.",
        session_id=session_id,
        document_id=document_id
    )

    assert first_result["session_id"] == session_id
    assert first_result["sources"]
    assert first_result["sources"][0]["document_id"] == document_id

    # Step 4: Follow-up question in the same session.
    second_result = chat_service.process_chat(
        question="Does it support OOP?",
        session_id=session_id,
        document_id=document_id
    )

    assert second_result["session_id"] == session_id
    assert second_result["search_query"] == (
        "Does Python support object-oriented programming?"
    )

    # Step 5: Verify actual Redis conversation history.
    history = chat_memory.get_history(session_id)

    assert len(history) == 4

    assert history[0]["role"] == "user"
    assert history[0]["content"] == "Tell me about Python."

    assert history[1]["role"] == "assistant"

    assert history[2]["role"] == "user"
    assert history[2]["content"] == "Does it support OOP?"

    assert history[3]["role"] == "assistant"

