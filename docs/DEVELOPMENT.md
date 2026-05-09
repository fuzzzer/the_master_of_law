# Development Guide

> Guide for contributing to The Master of Law.

## 1. Code Style and Conventions

We emphasize simplicity and directness over excessive abstraction.

- **Python (Backend):** 
  - Use `black` and `isort` for formatting.
  - Use type hints for all function arguments and return values.
  - Follow the `Route → Service → Repository` pattern.
- **Dart/Flutter (Frontend):** 
  - Follow standard `dart format`.
  - Use BLoC/Cubit for state management.
  - Follow the case-centric design paradigm.
- **Naming:** Must be descriptive. If a name needs a comment to explain what it does, the name is wrong.

## 2. How to Add a New Endpoint

To add a new endpoint, follow the layer architecture:

1. **Model/Schema:** Define request/response models in `backend/schemas/`. If it requires a database table, define the SQLAlchemy model in `backend/models/` and run an Alembic migration (`alembic revision --autogenerate -m "..."`).
2. **Repository:** Add database access logic in a new or existing repository in `backend/repositories/`.
3. **Service:** Add business logic in `backend/services/`. The service should take data from the route and use repositories to interact with the DB.
4. **Route:** Add the route in `backend/routes/`. Use Dependency Injection to inject the required service.
5. **Main:** Include the router in `backend/main.py`.

## 3. How to Add a New Service

Services encapsulate business logic:
1. Create a new file in `backend/services/` (e.g., `my_new_service.py`).
2. Define a class that takes its dependencies (repositories, other services, API clients) via `__init__`.
3. Write clean, focused methods.
4. If it interacts with the Gemini API, use the `google-genai` SDK and properly handle Vertex AI settings.

## 4. How to Modify the RAG Pipeline

The RAG pipeline is implemented in the `RAG Retrieval` service.
- **Feature Flags:** The pipeline uses `RAGCollectionConfig` to determine which ChromaDB collections to search.
- **Stages:** Modify `backend/services/rag_service.py` (or similar depending on current codebase structure) to tweak the 5 stages: Query Expansion, Vector Search, Full-Text Search, Merge, Rerank.
- **Prompts:** If you need to adjust instructions, update the prompt templates located in `backend/app/prompts/`.

## 5. How to Update the Legal Corpus

The law corpus resides in `law_corpus/data/chroma`.
**Warning:** Only update the corpus using the established scraping and chunking scripts.
1. Run the matsne scraping pipeline to fetch new data.
2. Chunk the text using the existing chunking algorithms to preserve semantic meaning.
3. Embed the chunks using `gemini-embedding-001`.
4. Ensure you use `task_type=RETRIEVAL_DOCUMENT` when inserting into ChromaDB.
See [LAW_CORPUS.md](LAW_CORPUS.md) for deeper details.

## 6. How to Run Tests

### Backend Tests
The backend uses `pytest`. Make sure your virtual environment is active.
```bash
cd backend
python -m pytest tests/ -v
```

## 7. How to Use the Eval Pipeline

The eval pipeline runs 50 real Supreme Court cases through the LLM.
Always use `holdout_eval.py` to prevent data contamination before running evaluations!

```bash
cd the_master_of_law

# 1. Hold out the evaluation cases from ChromaDB
python3 eval/test_cases/holdout_eval.py holdout

# 2. Run the evaluation
python3 eval/test_cases/run_eval.py

# 3. Restore the evaluation cases
python3 eval/test_cases/holdout_eval.py restore
```
Read the detailed guide in `eval/steps.md`.

## 8. Git Workflow

- **Branching:** Use descriptive branch names: `feature/add-credit-gate`, `bugfix/fix-rag-merge`.
- **Commits:** Write clear, concise commit messages.
- **PRs:** Describe *why* the change is made, not just *what* it is. Ensure all tests pass and documentation is updated before requesting a review.

## 9. Common Debugging Scenarios

- **ChromaDB Telemetry Errors:** You might see posthog errors in the logs. These are harmless, ignore them.
- **Missing or Incorrect Citations:** If the AI hallucinates a citation, check if `task_type=RETRIEVAL_QUERY` was used for the search embedding. Consistency between document and query embeddings is critical.
- **Georgian Text Issues:** Ensure everything handles UTF-8 encoding (Mkhedruli U+10D0–U+10FF).
- **Authentication Bypass in Dev:** In development mode, the system might mock the ADMIN user if Firebase tokens are not provided. Keep this in mind when testing tiered logic.
