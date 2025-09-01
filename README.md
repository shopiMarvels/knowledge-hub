# MCP Knowledge Hub

An **open‑source, MCP‑powered AI Knowledge Hub** that ingests documents/APIs, auto‑tags and summarizes content, and lets you **ask natural‑language questions with citations**. Built entirely on a **free, local‑first stack**.

---

## ✨ Features (MVP → v0.1)

* 📥 **Ingestion**: Upload PDFs/Docs (Day 2), parse → chunk → embed
* 🏷️ **Auto‑Tagging**: Topic labels per chunk/document (coming)
* 📝 **Summaries**: Map‑reduce summaries per document (coming)
* 🔎 **Semantic Search**: FAISS ANN + metadata filters (coming)
* 💬 **Q\&A with Citations**: Local LLM synthesis grounded on retrieved chunks (coming)
* 🧩 **MCP Agents**: Ingestion, Tagging, Summary, Q\&A — modular tool calls
* 🔐 **Local‑first**: Ollama for LLM/embeddings; no data leaves your machine

---

## 🧱 Tech Stack (100% Free / OSS)

* **Frontend**: Next.js 14 (App Router) + Tailwind (soon) + React Query
* **Backend**: FastAPI + Uvicorn
* **AI Runtime**: MCP agents + LangGraph/LCEL plumbing
* **LLMs/Embeddings**: Ollama (local Llama/Mistral); `sentence-transformers`
* **Vector Search**: FAISS (local)
* **Database**: PostgreSQL (metadata), Redis (queues/cache)
* **Workers**: RQ/Celery style worker (RQ scaffold)
* **Infra/Dev**: Docker, docker‑compose, GitHub Actions (CI)

---

## 🗺️ System Architecture (MVP)

```
+-------------+        HTTP(S)         +------------------+
|  Next.js    |  <------------------>  |   FastAPI API    |
|  Frontend   |                        |  (Auth, REST)     |
+------^------+                        +---------+--------+
       |  fetch /healthz, /search                |
       |                                          v
       |                                 +-------+--------+
       |                                 |   RAG Orchestr.|  (LangGraph)
       |                                 +-------+--------+
       |                                         |
       |            +----------------------------+----------------------+
       |            |                                                   |
       v            v                                                   v
+------+-----+  +---+---------------+                      +------------+-----+
|  Redis     |  |  MCP Agent Tools  |                      |   FAISS Index   |
|  (queues)  |  |  (parse, embed,   |                      |  (vectors on disk)|
+------------+  |   search, tag, …)  |                      +------------+-----+
                +---+---------------+                                   |
                    |                                                   |
                    v                                                   v
               +----+------------------+                     +----------+--------+
               |   PostgreSQL (meta)   |<------------------->|  Object Store/Disk |
               | users, docs, tags,... |     file paths      |  (uploads)         |
               +-----------------------+                     +--------------------+
```

---

## 🚀 Getting Started

### 1) Prerequisites

* Docker Desktop
* Node.js 20+, Python 3.11+
* Git

### 2) Clone & Structure

```bash
git clone <your-repo-url> knowledge-hub
cd knowledge-hub
# Expected structure
# apps/{api,web}  packages/{agents,db}  infra/
```

### 3) Environment

Create `.env` (or copy from example):

```bash
cp .env.example .env
```

**.env example**

```
NEXT_PUBLIC_API_URL=http://localhost:8000
APP_VERSION=0.1.0
```

### 4) Boot with Docker

```bash
docker compose -f infra/docker-compose.yml up --build -d
```

* Web → [http://localhost:3000](http://localhost:3000)
* API → [http://localhost:8000/healthz](http://localhost:8000/healthz)
* Postgres → `hub:hub@localhost:5432/hub`

### 5) (Optional) Run DB migration (Day 1)

```bash
cd apps/api
python -m venv .venv && source .venv/bin/activate  # use your OS equivalent
pip install -r requirements.txt
export DATABASE_URL=postgresql+psycopg://hub:hub@localhost:5432/hub
alembic upgrade head
```

> If you haven’t created the Alembic migration yet, see **/Day 1 — Scaffold & Hello World** in docs for the exact script. Future versions will auto‑migrate on start.

---

## 🧩 MCP Agents & Tools (planned interfaces)

* **file\_tool.read(path|bytes)** → PDF/DOCX/HTML to raw text (PyMuPDF, python‑docx)
* **chunk\_tool.split(text, size=800, overlap=120)** → RAG‑friendly chunks
* **embed\_tool.create(chunks, model=MiniLM)** → write FAISS + PG pointers
* **search\_tool.query(query, k=8)** → ANN + metadata join
* **tag\_tool.predict(chunks)** → topic labels (zero‑shot/local)
* **summary\_tool.summarize(doc\_id)** → map‑reduce + cache

Each tool exposes an **MCP schema** (name, args, returns). Agents are small state machines calling tools.

---

## 📡 API (initial)

* `GET /healthz` → `{ status, version }`
* `GET /version` → `{ version }`

**Coming soon**

* `POST /sources/upload` (multipart)
* `POST /ingest/{document_id}`
* `POST /search` `{ query, k }` → { hits }
* `POST /qa` `{ query, k }` → { answer, citations }

---

## 📁 Project Structure

```
knowledge-hub/
  apps/
    api/              # FastAPI app (Uvicorn, routes)
    web/              # Next.js app (App Router)
  packages/
    agents/           # Worker + MCP tool stubs
    db/               # SQLAlchemy models, Alembic migrations
  infra/
    docker-compose.yml
  .env.example
  README.md
```

---

## 🧪 Local Development

* **Hot‑reload**: web (Next.js dev) and api (Uvicorn `--reload`) are enabled in Dockerfiles
* **Logs**: `docker compose -f infra/docker-compose.yml logs -f api web worker`
* **DB shell**: `docker compose -f infra/docker-compose.yml exec db psql -U hub -d hub`
* **Stop**: `docker compose -f infra/docker-compose.yml down`

---

## 🗺️ Roadmap

* [ ] File uploads (PDF/DOC/DOCX/Markdown)
* [ ] Parsing + chunking pipeline (RQ worker)
* [ ] Embeddings + FAISS index build
* [ ] Semantic search endpoint + UI
* [ ] Q\&A with citations (Ollama → Llama3/Mistral)
* [ ] Auto‑tagging + summaries
* [ ] API connectors (GitHub README, Notion export, RSS)
* [ ] Rerankers (bge‑reranker‑base, local)
* [ ] Chat sessions, feedback signals, analytics

---

## 🤝 Contributing

PRs welcome! Please:

1. Open an issue describing the change
2. Follow the existing structure (apps/api, apps/web, packages/\*)
3. Keep the free/local‑first philosophy

> Dev containers/Makefile and CI checks coming soon.

---

## 🔒 Security & Privacy

* Local LLMs (Ollama) by default
* No external API calls required
* Optional PII scrubbing on ingest (regex)

---

## 📜 License

MIT — see `LICENSE`.

---

## 🙏 Acknowledgments

* MCP community & open tooling
* FAISS, sentence‑transformers, FastAPI, Next.js
* Everyone building **local‑first AI** ✨

---

## 📸 Screenshots (placeholders)

* `/app` home — API status ✅
* Upload → parse → summary (coming)
* Search/Chat with citations (coming)
