import asyncio
from dotenv import load_dotenv
load_dotenv()
from app.services.rag_retrieval_service import get_rag_service

async def main():
    rag = get_rag_service()
    chunks = await rag.retrieve("კანაფის ფისის ნარკოტიკის ზღვრები რაარის", collections=["georgian_laws"])
    
    thresholds = [c for c in chunks if c.get("metadata", {}).get("chunk_type") == "threshold"]
    print(f"Total chunks retrieved: {len(chunks)}")
    print(f"Threshold chunks retrieved: {len(thresholds)}")
    
    for i, c in enumerate(thresholds):
        print(f"[{i}] {c.get('chunk_id')} (Distance: {c.get('distance')})")

if __name__ == "__main__":
    asyncio.run(main())
