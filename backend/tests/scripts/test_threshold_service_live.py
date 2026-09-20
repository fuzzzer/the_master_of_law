import asyncio
from app.services.threshold_service import get_threshold_service
from app.services.rag_retrieval_service import get_rag_service
from app.services.legal_analysis_service import LawContextFormatter

async def main():
    rag = get_rag_service()
    chunks = await rag.retrieve("კანაფის ფისის (ჰაშიშის) ზღვრები")
    print(f"Chunks retrieved: {len(chunks)}")
    
    thresholds = [c for c in chunks if c.get("metadata", {}).get("chunk_type") == "threshold"]
    print(f"Thresholds found: {len(thresholds)}")
    for t in thresholds:
        print(">>", t["chunk_id"])

    fmt = LawContextFormatter()
    print("Formatted text length:", len(fmt.format(chunks)))
    print(fmt.format(chunks)[:1000])

if __name__ == "__main__":
    asyncio.run(main())
