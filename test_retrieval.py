from app.services.retrieval_service import retrieve_chunks


question = "What technical skills and programming languages are mentioned in the resume?"

results = retrieve_chunks(
    question=question,
    top_k=5,
    document_id=1
)

if not results:
    print("No relevant chunks found.")

for index, result in enumerate(results, start=1):
    print(f"\n--- Result {index} ---")
    print("Document:", result["filename"])
    print("Chunk:", result["chunk_index"])
    print("Similarity score:", result["score"])
    print("Content:", result["text"])