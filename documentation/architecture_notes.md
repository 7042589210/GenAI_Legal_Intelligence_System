# Architecture Notes

This document describes how the backend of the Tata Legal AI System handles its internal modules gracefully while remaining within a single Python package environment, bypassing the need for complicated namespace resolutions.

## Core Flow
1. **Document Processing (`backend/ingestion/` and `backend/preprocessing/`)**: Extracts raw text, normalizes tokens, and handles OCR.
2. **Data Schemas (`backend/schemas/` and `backend/database/models.py`)**: Houses Pydantic models for request/response validation and SQLAlchemy models.
3. **AI Workflows (`backend/workflows/`, `backend/legal_analysis/`, etc.)**: Core business logic chaining prompts to extract structure, build vector stores, and run RAG.
4. **Legal Operations (`backend/legal_operations/`)**: State machine handling human reviews and task queues.

**Integration Note**: 
Because we do not split these into separate root directories, they all share `backend` as their base module. This ensures `main.py` can directly route logic efficiently, completely circumventing cross-package cyclic imports.
