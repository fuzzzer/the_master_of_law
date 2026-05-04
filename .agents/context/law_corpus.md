# Law Corpus Context

> **Status:** ✅ Complete — DO NOT MODIFY
> **Location:** `law_corpus/`

## What It Is
Complete pipeline that scraped, parsed, chunked, embedded, and indexed 12 Georgian legal codes from matsne.gov.ge.

## Key Data
- **9,450 chunks** across **1,525 unique articles** in **12 legal codes**
- **ChromaDB** collection: `georgian_laws` at `law_corpus/data/chroma/`
- **768-dim vectors** via `gemini-embedding-001` with `task_type=RETRIEVAL_DOCUMENT`
- **Metadata per chunk:** `code_name`, `article_number`, `article_title`, `citation_text`, `source_url`, `article_url`, `document_number`

## Querying
```python
import chromadb
client = chromadb.PersistentClient(path="<path>/law_corpus/data/chroma")
collection = client.get_collection("georgian_laws")
results = collection.query(query_embeddings=[query_vector], n_results=50,
                           include=["documents", "metadatas", "distances"])
```
Query embeddings MUST use same model (gemini-embedding-001), 768 dims, `task_type=RETRIEVAL_QUERY`.

## Legal Codes Indexed
Constitution, Civil Code, Criminal Code, Civil Procedure, Criminal Procedure, Administrative Code, Administrative Procedure, Administrative Offences, Labour Code, Tax Code, General Administrative Code, Juvenile Justice Code
