# Knowledge Hub Demo Script (5 minutes)

## Setup
- Ensure all services are running: `docker compose -f knowledge-hub/infra/docker-compose.yml up -d`
- Have a PDF ready for upload
- Have a GitHub repo URL ready (e.g., https://github.com/microsoft/TypeScript)
- Have an RSS feed URL ready (e.g., https://feeds.feedburner.com/oreilly/radar)

## Demo Flow

### Intro (30 seconds)
> "Welcome to my MCP-powered AI Knowledge Hub. In just 7 days, I built a local-first, open-source system that transforms unstructured docs and APIs into organized, searchable insights."

**Show:** Homepage at http://localhost:3000

### Step 1: Upload & Ingest (90 seconds)

**Upload a Document:**
1. Navigate to Upload page
2. Upload a PDF document
3. Show the processing status and "View document" link

**Multi-Source Ingestion:**
1. Navigate to Ingest page
2. Demonstrate GitHub ingestion with a repo URL
3. Show RSS feed ingestion
4. Navigate to Dashboard to show all documents appearing

**Show:** Dashboard with multiple documents from different sources

### Step 2: Auto-Tagging & Summaries (60 seconds)

**Document Intelligence:**
1. Click on a document from the dashboard
2. Show the document detail page
3. Click "Run Auto-Tagging" - show tags appearing as chips
4. Click "Run Summarization" - show generated summary
5. Explain how this uses Ollama LLM locally

**Show:** Document page with tags and summary populated

### Step 3: Semantic Search (60 seconds)

**Intelligent Search:**
1. Navigate to Search page
2. Enter a natural language query related to uploaded content
3. Show FAISS-powered semantic search results
4. Highlight relevance scores and document snippets

**Show:** Search results with similarity scores and document previews

### Step 4: Q&A Chat (60 seconds)

**Grounded Q&A:**
1. Navigate to Chat page
2. Ask a specific question about the uploaded content
3. Show the AI-generated answer with citations
4. Click on citations to show they link back to source documents
5. Show context hits that were used to generate the answer

**Show:** Chat interface with cited answer and source links

### Wrap-up (30 seconds)
> "All of this runs 100% locally using Next.js, FastAPI, Postgres, Redis, FAISS, and Ollama. No vendor lock-in. It's a complete Retrieval-Augmented Generation system with tagging, summaries, and multi-source ingestion."

**Show:** Architecture overview or final dashboard view

## Key Points to Highlight

- **Local-first**: Everything runs on your machine
- **Open-source**: Built with standard tools, no proprietary APIs
- **Multi-modal**: Handles PDFs, GitHub repos, RSS feeds
- **AI-powered**: Semantic search, auto-tagging, Q&A with citations
- **Complete pipeline**: Upload → Parse → Chunk → Embed → Tag → Summarize → Search → Chat
- **Production-ready**: Docker deployment, proper database, job queues

## Technical Stack Mentioned
- **Frontend**: Next.js 14 with TypeScript and Tailwind CSS
- **Backend**: FastAPI with Python
- **Database**: PostgreSQL with SQLAlchemy
- **Search**: FAISS for vector similarity
- **AI**: Ollama for local LLM inference
- **Jobs**: Redis Queue (RQ) for background processing
- **Deployment**: Docker Compose

## Demo URLs
- Homepage: http://localhost:3000
- Dashboard: http://localhost:3000/dashboard
- Upload: http://localhost:3000/upload
- Ingest: http://localhost:3000/ingest
- Search: http://localhost:3000/search
- Chat: http://localhost:3000/chat
- API Health: http://localhost:8000/healthz
- API Docs: http://localhost:8000/docs
