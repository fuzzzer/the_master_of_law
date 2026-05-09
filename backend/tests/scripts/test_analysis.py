import asyncio
from app.services.rag_retrieval_service import get_rag_service
from app.services.legal_analysis_service import get_legal_analysis_service

async def main():
    rag = get_rag_service()
    chunks = await rag.retrieve("კანაფის ფისის ნარკოტიკის ზღვრები რაარის")
    print(f"Retrieved {len(chunks)} chunks")
    
    thresholds = [c for c in chunks if c.get("metadata", {}).get("chunk_type") == "threshold"]
    print(f"Thresholds: {len(thresholds)}")
    for t in thresholds:
        print(t.get("chunk_id"), t.get("content")[:100].replace("\n", " "))
        
    analysis_svc = get_legal_analysis_service()
    formatted = analysis_svc._law_formatter.format(chunks)
    print("FORMATTED CONTEXT:")
    print(formatted[:1000])

if __name__ == "__main__":
    asyncio.run(main())
