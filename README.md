# Tata Legal AI Intelligence System

A robust, AI-powered legal contract analysis and human-in-the-loop operations system.

## 🚀 Project Overview
The Tata Legal AI Intelligence System automates the ingestion, analysis, and processing of complex legal documents (PDFs, DOCX). It leverages advanced OCR and LLM-driven workflows to extract clauses, perform risk assessments, and instantly map findings into a searchable vector database.

### 🏗️ Architecture & Component Breakdown
The system is built on a clean, scalable architecture:
*   **Frontend**: Streamlit-based interactive UI.
*   **Backend**: High-performance FastAPI server serving REST endpoints.
*   **Document Processing**: OCR-powered text extraction pipeline handling raw native and scanned documents.
*   **AI Workflows**: LLM reasoning engine (Llama 3 via Groq) combined with RAG to analyze and evaluate contracts.
*   **Data Schemas**: Unified Pydantic and SQLAlchemy models ensuring strict data validation.
*   **Vector DB**: ChromaDB for semantic search across ingested documents.

## 💻 Local Setup (Without Docker)

1. **Clone and create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
2. **Install dependencies:**
   ```bash
   pip install -r backend/requirements.txt
   ```
3. **Configure Environment:**
   Copy `.env.example` to `.env` and fill in your keys (e.g., `GROQ_API_KEY`).
4. **Run the services:**
   *   **Backend**: `uvicorn backend.main:app --reload`
   *   **Frontend**: `streamlit run frontend/app.py`

## 🐳 Local Setup (With Docker)
Just run Docker Compose from the root directory:
```bash
docker-compose up --build
```
This boots the backend and sets up data persistence for SQLite and ChromaDB automatically.

## 🌍 Deployment Guide

### Deploying the Backend (Render / Railway)
The project includes `deployment/render.yaml` and `deployment/railway.json` for easy 1-click deployments.
1. Connect your GitHub repository to Render/Railway.
2. Select the repository and the deployment platform will auto-detect the configuration.
3. Add your `GROQ_API_KEY` to the Environment Variables.

### Deploying the Frontend (Vercel / Netlify / Streamlit Cloud)
1. Link your repository to Streamlit Community Cloud (or Vercel).
2. Set the entrypoint to `frontend/app.py`.
3. Add an environment variable pointing to your deployed backend URL.

## 🔌 API Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/analyze-contract` | POST | Upload and process a legal document |
| `/api/cases` | GET | List all active legal review cases |
| `/api/cases/{id}` | GET | Retrieve a specific case by ID |
| `/api/cases/{id}/review` | POST | Submit human review decision |

---
*Generated for internal deployment preparation.*
