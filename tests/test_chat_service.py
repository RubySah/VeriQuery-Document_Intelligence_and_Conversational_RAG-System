
from unittest.mock import Mock
from uuid import UUID

import pytest

from app.services import chat_service


@pytest.fixture
def setup_chat_service(monkeypatch):
    memory = Mock()
    llm = Mock()
    retrieval = Mock()

    monkeypatch.setattr(
        chat_service,
        "chat_memory",
        memory
    )
    monkeypatch.setattr(
        chat_service,
        "llm_service",
        llm
    )
    monkeypatch.setattr(
        chat_service,
        "retrieve_chunks",
        retrieval
    )

    memory.get_history.return_value = []

    retrieval.return_value = [
        {
            "document_id": 1,
            "filename": "sample.pdf",
            "chunk_index": 0,
            "text": "Python is a programming language.",
            "score": 0.91
        }
    ]

    llm.generate_answer.return_value = (
        "Python is a programming language."
    )

    return memory, llm, retrieval


def test_new_chat_session(
    setup_chat_service
):
    memory, llm, retrieval = setup_chat_service

    result = chat_service.process_chat(
        question="What is Python?"
    )

    # A valid new UUID should be generated.
    UUID(result["session_id"])

    assert result["question"] == "What is Python?"
    assert result["search_query"] == "What is Python?"
    assert result["answer"] == (
        "Python is a programming language."
    )

    # No history means no query rewriting.
    llm.rewrite_question.assert_not_called()

    retrieval.assert_called_once_with(
        question="What is Python?",
        top_k=5,
        document_id=None
    )

    llm.generate_answer.assert_called_once()

    memory.add_exchange.assert_called_once_with(
        session_id=result["session_id"],
        question="What is Python?",
        answer="Python is a programming language."
    )


def test_existing_session_rewrites_followup_question(
    setup_chat_service
):
    memory, llm, retrieval = setup_chat_service

    session_id = "31fc6666-4453-4e54-8b1c-7f96340b4e97"

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

    memory.get_history.return_value = history

    llm.rewrite_question.return_value = (
        "What are the main features of Python?"
    )

    result = chat_service.process_chat(
        question="What are its main features?",
        session_id=session_id
    )

    assert result["session_id"] == session_id

    llm.rewrite_question.assert_called_once_with(
        question="What are its main features?",
        conversation_history=history
    )

    retrieval.assert_called_once_with(
        question="What are the main features of Python?",
        top_k=5,
        document_id=None
    )

    assert result["search_query"] == (
        "What are the main features of Python?"
    )


def test_document_id_is_passed_to_retrieval(
    setup_chat_service
):
    memory, llm, retrieval = setup_chat_service

    result = chat_service.process_chat(
        question="Explain this document.",
        document_id=42
    )

    retrieval.assert_called_once_with(
        question="Explain this document.",
        top_k=5,
        document_id=42
    )

    assert result["sources"][0]["document_id"] == 1


def test_empty_question_is_rejected(
    setup_chat_service
):
    memory, llm, retrieval = setup_chat_service

    with pytest.raises(
        ValueError,
        match="Question cannot be empty"
    ):
        chat_service.process_chat(
            question="   "
        )

    memory.get_history.assert_not_called()
    retrieval.assert_not_called()
    llm.generate_answer.assert_not_called()


def test_empty_rewritten_query_falls_back_to_original(
    setup_chat_service
):
    memory, llm, retrieval = setup_chat_service

    memory.get_history.return_value = [
        {
            "role": "user",
            "content": "Tell me about Python."
        }
    ]

    llm.rewrite_question.return_value = "   "

    result = chat_service.process_chat(
        question="What about its features?",
        session_id="test-session"
    )

    assert result["search_query"] == (
        "What about its features?"
    )

    retrieval.assert_called_once_with(
        question="What about its features?",
        top_k=5,
        document_id=None
    )


def test_empty_retrieval_results(
    setup_chat_service
):
    memory, llm, retrieval = setup_chat_service

    retrieval.return_value = []

    llm.generate_answer.return_value = (
        "I couldn't find relevant information."
    )

    result = chat_service.process_chat(
        question="What is quantum computing?"
    )

    assert result["sources"] == []

    llm.generate_answer.assert_called_once_with(
        question="What is quantum computing?",
        retrieved_chunks=[],
        conversation_history=[]
    )

    assert result["answer"] == (
        "I couldn't find relevant information."
    )


def test_sources_are_formatted_correctly(
    setup_chat_service
):
    memory, llm, retrieval = setup_chat_service

    retrieval.return_value = [
        {
            "document_id": 5,
            "filename": "report.pdf",
            "chunk_index": 2,
            "text": "Relevant content.",
            "score": 0.88
        },
        {
            "document_id": None,
            "filename": None,
            "chunk_index": None,
            "text": "Incomplete payload.",
            "score": None
        }
    ]

    result = chat_service.process_chat(
        question="Summarize the report."
    )

    assert result["sources"] == [
        {
            "document_id": 5,
            "filename": "report.pdf",
            "chunk_index": 2,
            "score": 0.88
        }
    ]


def test_history_is_loaded_before_processing(
    setup_chat_service
):
    memory, llm, retrieval = setup_chat_service

    memory.get_history.return_value = [
        {
            "role": "user",
            "content": "Previous question."
        }
    ]

    llm.rewrite_question.return_value = "Standalone query"

    chat_service.process_chat(
        question="Follow-up question?",
        session_id="test-session"
    )

    memory.get_history.assert_called_once_with(
        "test-session"
    )


def test_exchange_is_not_saved_if_answer_generation_fails(
    setup_chat_service
):
    memory, llm, retrieval = setup_chat_service

    llm.generate_answer.side_effect = RuntimeError(
        "LLM generation failed"
    )

    with pytest.raises(
        RuntimeError,
        match="LLM generation failed"
    ):
        chat_service.process_chat(
            question="What is Python?"
        )

    memory.add_exchange.assert_not_called()
