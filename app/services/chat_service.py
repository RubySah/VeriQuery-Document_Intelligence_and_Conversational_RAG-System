
from uuid import uuid4

from app.services.chat_memory import chat_memory
from app.services.llm_service import llm_service
from app.services.retrieval_service import retrieve_chunks


def process_chat(
    question: str,
    session_id: str | None = None,
    document_id: int | None = None
) -> dict:
    if not question.strip():
        raise ValueError("Question cannot be empty.")

    # Create a new conversation if no session ID was provided.
    if not session_id:
        session_id = str(uuid4())

    # Step 1: Retrieve previous conversation messages.
    history = chat_memory.get_history(session_id)

    # Step 2: Convert follow-up questions into standalone queries.
    search_query = llm_service.rewrite_question(
        question=question,
        conversation_history=history
    )

    # Step 3: Retrieve relevant document chunks.
    chunks = retrieve_chunks(
        question=search_query,
        top_k=5,
        document_id=document_id
    )

    # Step 4: Generate an answer using retrieved context and history.
    answer = llm_service.generate_answer(
        question=question,
        retrieved_chunks=chunks,
        conversation_history=history
    )

    # Step 5: Save the successful interaction in Redis.
    chat_memory.add_message(
        session_id=session_id,
        role="user",
        content=question
    )

    chat_memory.add_message(
        session_id=session_id,
        role="assistant",
        content=answer
    )

    return {
        "session_id": session_id,
        "question": question,
        "search_query": search_query,
        "answer": answer,
        "sources": [
            {
                "document_id": chunk["document_id"],
                "filename": chunk["filename"],
                "chunk_index": chunk["chunk_index"],
                "score": chunk["score"]
            }
            for chunk in chunks
        ]
    }
