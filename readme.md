
# Palm Mind — AI-Powered Document Intelligence & Conversational RAG

An AI-powered document intelligence backend that transforms uploaded documents into searchable knowledge and enables context-aware conversations using Retrieval-Augmented Generation (RAG).

Built with **FastAPI, Google Gemini, Sentence Transformers, Qdrant, PostgreSQL, and Redis**.

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi" alt="FastAPI">
  <img src="https://img.shields.io/badge/LLM-Google%20Gemini-4285F4?logo=google" alt="Gemini">
  <img src="https://img.shields.io/badge/Vector%20DB-Qdrant-DC382D" alt="Qdrant">
  <img src="https://img.shields.io/badge/Database-PostgreSQL-4169E1?logo=postgresql" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/Cache-Redis-DC382D?logo=redis" alt="Redis">
</p>

---

## Overview

Palm Mind is a modular backend application designed to make document-based information retrieval more intelligent and interactive.

Users can upload PDF or TXT documents, which are processed into smaller chunks, converted into vector embeddings, and stored in a vector database. The system retrieves relevant information based on user queries and generates context-aware responses using Google Gemini.

Beyond basic document question answering, Palm Mind supports multi-turn conversations through Redis-based chat memory and includes an AI-powered interview booking workflow that extracts, validates, and persists booking information.

## Key Features

### 1. Document Ingestion
- Supports PDF and TXT document uploads.
- Extracts text using PyMuPDF.
- Supports fixed-size and paragraph-based chunking strategies.
- Generates vector embeddings using Sentence Transformers.
- Stores document metadata in PostgreSQL.
- Stores document chunks and embeddings in Qdrant.

### 2. Semantic Search & Retrieval-Augmented Generation
- Performs semantic similarity search using Qdrant.
- Retrieves the most relevant document chunks.
- Supports filtering retrieval by document ID.
- Generates context-aware responses using Google Gemini.
- Includes retrieved source information in responses.
- Uses a custom RAG pipeline rather than a prebuilt RetrievalQA chain.

### 3. Conversational AI with Redis Memory
- Maintains session-based conversation history.
- Stores recent messages in Redis.
- Rewrites follow-up questions into standalone queries using conversation context.
- Supports multi-turn interactions.
- Automatically expires inactive conversation history.

### 4. AI-Powered Interview Booking
- Extracts candidate information from chat conversations.
- Identifies name, email, interview date, and time.
- Validates extracted information and timezone.
- Separates information extraction from booking confirmation.
- Persists confirmed booking requests in PostgreSQL.
- Uses database-level uniqueness constraints and upsert operations to prevent duplicate bookings for the same session.

### 5. API & Documentation
- RESTful APIs built with FastAPI.
- Interactive Swagger documentation.
- ReDoc API documentation.
- Professional project landing page.
- Health-check endpoint.

---

## System Architecture

The application follows a modular service-oriented architecture.

```mermaid
flowchart TB
    Client[API Client]
    API[FastAPI Application]

    Client --> API

    API --> Documents[Document API]
    API --> Chat[Chat API]
    API --> Booking[Booking API]

    Documents --> Ingestion[Document Ingestion Service]
    Ingestion --> Extraction[Text Extraction]
    Extraction --> Chunking[Chunking Service]
    Chunking --> Embedding[Embedding Service]
    Embedding --> Qdrant[(Qdrant)]
    Ingestion --> PostgreSQL[(PostgreSQL)]

    Chat --> ChatService[Chat Service]
    ChatService --> Redis[(Redis Memory)]
    ChatService --> Retrieval[Retrieval Service]
    Retrieval --> Embedding
    Retrieval --> Qdrant
    ChatService --> Gemini[Google Gemini]

    Booking --> BookingService[Booking Service]
    BookingService --> Redis
    BookingService --> Validation[Booking Validation]
    BookingService --> PostgreSQL
```

For detailed component descriptions and workflow diagrams, see [ARCHITECTURE.md](ARCHITECTURE.md).

---

## Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.13 | Core programming language |
| FastAPI | Backend API framework |
| Google Gemini | LLM-powered response generation and information extraction |
| Sentence Transformers | Local text embedding generation |
| all-MiniLM-L6-v2 | 384-dimensional embedding model |
| Qdrant | Vector database and semantic retrieval |
| PostgreSQL | Relational database for metadata and bookings |
| SQLAlchemy | ORM and database operations |
| Redis | Conversation memory and session management |
| PyMuPDF | PDF text extraction |
| Pydantic | Data validation and settings management |
| Pytest | Unit and integration testing |
| Docker Compose | Local infrastructure management |

---

```text
palmind-rag-backend/
│
├── app/
│   ├── main.py
│   │
│   ├── api/
│   │   ├── documents.py
│   │   ├── chat.py
│   │   └── bookings.py
│   │
│   ├── core/
│   │   └── config.py
│   │
│   ├── database/
│   │   ├── database.py
│   │   ├── init_db.py
│   │   ├── models.py
│   │   └── qdrant.py
│   │
│   ├── schemas/
│   │   ├── chat.py
│   │   └── booking.py
│   │
│   ├── services/
│   │   ├── document_extraction.py
│   │   ├── chunking_service.py
│   │   ├── embedding_service.py
│   │   ├── document_service.py
│   │   ├── retrieval_service.py
│   │   ├── chat_memory.py
│   │   ├── llm_service.py
│   │   ├── chat_service.py
│   │   ├── booking_service.py
│   │   └── booking_validation.py
│   │
│   └── templates/
│       └── index.html
│
├── tests/
│   ├── integration/
│   │   ├── conftest.py
│   │   ├── test_api_workflow.py
│   │   ├── test_booking_integration.py
│   │   ├── test_chat_integration.py
│   │   └── test_document_pipeline.py
│   │
│   ├── test_booking_service.py
│   ├── test_booking_validation.py
│   ├── test_chat_api.py
│   ├── test_chat_memory.py
│   ├── test_chat_service.py
│   ├── test_chunking_service.py
│   ├── test_document_extraction.py
│   ├── test_document_service.py
│   ├── test_live_gemini.py
│   └── test_retrieval_service.py
│
├── docker-compose.yml
├── requirements.txt
├── pytest.ini
├── .env.example
├── .gitignore
├── README.md
└── ARCHITECTURE.md

```
---

## Getting Started

### Prerequisites

Make sure you have installed:

- Python 3.13
- Docker Desktop and Docker Compose
- Git
- Google Gemini API key

### 1. Clone the repository

```bash
git clone https://github.com/RubySah/palm-mind-ai-rag-backend

cd YOUR_REPOSITORY
```

Replace the URL with your actual GitHub repository URL.

### 2. Create a virtual environment

**Windows CMD:**

```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**Linux / macOS:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root using `.env.example` as a reference.

Configure your Gemini API key and the database/service connection settings.

Example connection settings (adjust names and values to match `app/core/config.py`):

```env
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=your_configured_gemini_model

DATABASE_URL=postgresql+psycopg://postgres:your_password@localhost:5433/palmind_db

REDIS_URL=redis://localhost:6379/0

QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=palmind_documents

EMBEDDING_MODEL=all-MiniLM-L6-v2
```

**Important:** Never commit your `.env` file or expose API credentials publicly.

### 5. Start infrastructure services

Start PostgreSQL, Redis, and Qdrant using Docker Compose:

```bash
docker compose up -d
```

Verify the services:

```bash
docker compose ps
```

Default local ports used by this project:

| Service | Port |
|---|---:|
| PostgreSQL | 5433 |
| Redis | 6379 |
| Qdrant HTTP | 6333 |
| Qdrant gRPC | 6334 |

### 6. Initialize the database

Create the PostgreSQL database configured in your environment.

Then initialize the application tables:

```bash
python -m app.database.init_db
```

Ensure the Qdrant collection is initialized using the application's configured collection.

### 7. Run the application

```bash
uvicorn app.main:app --reload
```

The application will be available at:

**http://127.0.0.1:8000**

---

## API Endpoints

Interactive API documentation is available through Swagger UI.

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Project landing page |
| GET | `/health` | Application health check |
| POST | `/documents/upload` | Upload and process PDF/TXT documents |
| POST | `/chat/` | Ask questions using conversational RAG |
| POST | `/bookings/extract` | Extract interview details from a conversation |
| POST | `/bookings/confirm` | Confirm and persist booking details |

### API Documentation

| Interface | URL |
|---|---|
| Swagger UI | `/docs` |
| ReDoc | `/redoc` |

### Example: Document Upload

```bash
curl -X POST "http://127.0.0.1:8000/documents/upload?strategy=fixed" \
  -F "file=@sample.pdf"
```

Supported chunking strategies:

- `fixed`
- `paragraph`

### Example: Chat Request

```json
{
  "question": "What are the main topics discussed in the document?",
  "session_id": null,
  "document_id": 1
}
```

The returned `session_id` can be reused to maintain conversation context across subsequent requests.

### Example: Interview Booking Extraction

```json
{
  "session_id": "00000000-0000-0000-0000-000000000000",
  "timezone_name": "Asia/Kathmandu"
}
```

The extraction endpoint returns the identified booking details and any missing fields. It does not save the booking.

### Example: Booking Confirmation

```json
{
  "session_id": "00000000-0000-0000-0000-000000000000",
  "booking": {
    "name": "Example Candidate",
    "email": "candidate@example.com",
    "interview_date": "2026-12-15",
    "interview_time": "14:30",
    "timezone_name": "Asia/Kathmandu"
  }
}
```

A successful response indicates that the booking request has been stored with `pending` status. It does not mean an organizer has confirmed the interview.

---

## Testing

The project includes unit tests, integration tests, and optional live Gemini API tests.

### Run unit tests

```bash
pytest -v tests
```

### Run integration tests

```bash
pytest -v tests/integration
```

Integration tests require dedicated PostgreSQL, Redis, and Qdrant test resources.

For Windows CMD, configure:

```cmd
set TEST_DATABASE_URL=postgresql+psycopg://postgres:your_password@127.0.0.1:5433/palmind_test_db

set TEST_REDIS_URL=redis://localhost:6379/1

set TEST_QDRANT_COLLECTION=palmind_integration_test
```

**Warning:** The integration test fixtures reset test Redis/Qdrant resources and create/drop database tables. Never point these settings at production or valuable development data.

### Run live Gemini tests

These tests make actual calls to the Gemini API and require a valid API key.

```cmd
set RUN_LIVE_GEMINI=1

pytest -v tests/test_live_gemini.py

set RUN_LIVE_GEMINI=
```

---

## Engineering Decisions

- **Custom RAG implementation:** Retrieval, context construction, prompt handling, and response generation are implemented as separate services instead of relying on a prebuilt RetrievalQA chain.
- **Local embeddings:** Sentence Transformers generates embeddings locally, avoiding a separate embedding API dependency.
- **Specialized storage:** PostgreSQL handles relational records, Qdrant handles vector search, and Redis handles short-lived conversation memory.
- **Explicit booking confirmation:** Extracted details are not persisted until the confirmation endpoint is called.
- **Modular architecture:** API routes, schemas, database operations, and business logic are separated for maintainability and testing.

## Current Limitations

- The homepage is informational; there is no separate interactive chat frontend.
- The `/health` endpoint is a basic application health response, not a full dependency readiness check.
- PostgreSQL and Qdrant do not share a distributed transaction, so failure recovery during document ingestion can require reconciliation.
- Prompt-injection defenses are not guaranteed by prompt instructions alone.

## Future Improvements

- Add authentication and role-based access control.
- Implement document deletion and vector cleanup.
- Add background document processing.
- Implement dependency-aware health checks.
- Add monitoring, structured logging, and request tracing.
- Improve cross-database consistency with an outbox or reconciliation mechanism.
- Add booking availability and scheduling conflict checks.
- Build an interactive frontend.

---

## Author

**Ruby Kumari Sah**

Developed as an AI/ML backend engineering project.
