# Persian RAG Chatbot

A production-ready Retrieval-Augmented Generation (RAG) chatbot built with **FastAPI**.  
Upload Persian/Farsi documents (PDF, Word, scanned images) — the system extracts, normalizes, embeds, and indexes the content into a Qdrant vector database so users can query it in natural language.

## Features

- **Multi-format ingestion** — PDF (native text + automatic OCR fallback for scanned pages), Word (`.docx`), and images (`.png`, `.jpg`, etc.)
- **Persian text normalization** — strips diacritics, maps Arabic look-alike characters to Persian equivalents, collapses redundant whitespace
- **Multilingual embeddings** — `paraphrase-multilingual-MiniLM-L12-v2` natively supports Persian/Farsi and 50+ other languages
- **Overlapping chunks** — sliding-window word chunker carries context across chunk boundaries for better retrieval recall
- **URL preservation** — English URLs embedded in Persian documents are extracted and returned alongside answers
- **Qdrant vector store** — fast cosine-similarity search
- **OpenAI LLM** — grounded answer generation with a strict RAG prompt
- **FastAPI** — async REST API with automatic OpenAPI docs, dependency injection, and startup lifespan validation

## Tech Stack

| Layer | Technology |
|---|---|
| API framework | FastAPI + Uvicorn |
| Document reading | PyMuPDF, python-docx, Pillow |
| OCR | Tesseract (`fas+eng`) via pytesseract |
| Text normalization | Custom Persian normalizer |
| Embeddings | `sentence-transformers` — multilingual MiniLM |
| Vector store | Qdrant |
| LLM | OpenAI (`gpt-4o-mini`) |
| Config | python-dotenv |

## Project Structure

```
ChatBot2/
├── app/
│   ├── main.py              ← FastAPI app instance, router registration, lifespan
│   ├── config.py            ← All settings, loaded from .env
│   ├── dependencies.py      ← FastAPI dependency injection providers
│   ├── schemas.py           ← Pydantic request / response models
│   │
│   ├── api/
│   │   ├── chat.py          ← POST /chat
│   │   └── ingest.py        ← POST /ingest
│   │
│   ├── ingestion/
│   │   ├── readers.py       ← PDF / Word / Image file readers
│   │   ├── normalizer.py    ← Persian text cleaning and normalization
│   │   └── chunker.py       ← Sliding-window overlapping word chunker
│   │
│   ├── rag/
│   │   ├── retriever.py     ← Semantic search → context + sources + URLs
│   │   └── generator.py     ← OpenAI grounded answer generation
│   │
│   └── vectorstore/
│       ├── embedder.py      ← Multilingual sentence-transformer wrapper
│       └── qdrant_store.py  ← Qdrant collection management, upsert, search
│
├── scripts/
│   ├── ingest.py            ← CLI: batch document ingestion pipeline
│   └── chat.py              ← CLI: interactive terminal chat session
│
├── requirements.txt
├── .env.example
└── .gitignore
```

## Setup

### Prerequisites

- Python 3.10+
- [Qdrant](https://qdrant.tech/) running locally (Docker recommended)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) with the Persian language pack (`fas`)
- An OpenAI API key

### 1. Clone and install

```bash
git clone https://github.com/your-username/ChatBot2.git
cd ChatBot2
pip install -r requirements.txt
```

### 2. Start Qdrant

```bash
docker run -p 6333:6333 qdrant/qdrant
```

### 3. Configure environment

```bash
cp .env.example .env
# Open .env and set at minimum: OPENAI_API_KEY
```

### 4. Install Tesseract with Persian support

**Windows** — Download from [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki) and select the Farsi language pack during installation.

**Linux:**
```bash
sudo apt install tesseract-ocr tesseract-ocr-fas
```

**macOS:**
```bash
brew install tesseract tesseract-lang
```

## Usage

### Start the API server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Interactive API docs: **http://localhost:8000/docs**

### Ingest documents (CLI)

```bash
# Single file
python scripts/ingest.py path/to/document.pdf

# Entire folder (recursive)
python scripts/ingest.py path/to/documents/ --recursive

# Rebuild the collection from scratch
python scripts/ingest.py path/to/documents/ --recursive --recreate
```

### Chat in the terminal (CLI)

```bash
python scripts/chat.py
python scripts/chat.py --top-k 8
```

```
────────────────────────────────────────────────────────────
  Persian RAG Chatbot
────────────────────────────────────────────────────────────

Collection 'knowledge_base' — 1240 indexed chunks.
Type your question and press Enter. Type 'quit' or 'exit' to stop.

You: چه اطلاعاتی درباره قرارداد وجود دارد؟
Bot: بر اساس اسناد موجود، قرارداد شامل ...

Sources (1):
  • documents/contract.pdf
```

### REST API

**POST `/chat`**
```json
{
  "query": "what is the contract deadline?",
  "top_k": 5
}
```

**POST `/ingest`**  
Upload a file via `multipart/form-data` — accepted types: `.pdf`, `.docx`, `.doc`, `.png`, `.jpg`, `.jpeg`, `.tiff`, `.bmp`, `.webp`

**GET `/health`**
```json
{
  "status": "ok",
  "qdrant": "reachable",
  "collection": "knowledge_base",
  "embedding_model": "paraphrase-multilingual-MiniLM-L12-v2"
}
```

## Configuration

All values can be overridden in `.env`:

| Variable | Default | Description |
|---|---|---|
| `QDRANT_HOST` | `localhost` | Qdrant server host |
| `QDRANT_PORT` | `6333` | Qdrant server port |
| `COLLECTION_NAME` | `knowledge_base` | Qdrant collection name |
| `EMBEDDING_MODEL` | `paraphrase-multilingual-MiniLM-L12-v2` | Sentence-transformer model |
| `VECTOR_SIZE` | `384` | Embedding dimensions (must match model) |
| `OPENAI_API_KEY` | — | Your OpenAI API key |
| `LLM_MODEL` | `gpt-4o-mini` | OpenAI model for answer generation |
| `TESSERACT_CMD` | Windows default path | Path to Tesseract executable |
| `OCR_LANG` | `fas+eng` | Tesseract language(s) |
| `CHUNK_SIZE` | `200` | Words per chunk |
| `CHUNK_OVERLAP` | `30` | Overlapping words between consecutive chunks |
| `OCR_FALLBACK_THRESHOLD` | `50` | Min chars on a PDF page before OCR is used |

## How it works

```
Documents (PDF / Word / Image)
         │
         ▼
  ingestion/readers.py     ← extract raw text; OCR fallback for scanned pages
         │
         ▼
  ingestion/normalizer.py  ← clean Persian text, strip diacritics, map chars
         │
         ▼
  ingestion/chunker.py     ← split into overlapping word windows
         │
         ▼
  vectorstore/embedder.py  ← multilingual sentence-transformer (384-dim)
         │
         ▼
  vectorstore/qdrant_store ← store vectors + metadata (source, page, urls)

── At query time ──────────────────────────────────────────────────────────────

  User question
         │
         ▼
  vectorstore/embedder.py  ← embed the query
         │
         ▼
  vectorstore/qdrant_store ← top-k cosine similarity search
         │
         ▼
  rag/generator.py         ← GPT answer grounded in retrieved context
         │
         ▼
  Answer + Sources + URLs
```

## License

MIT
