import asyncio
from app.services.rag_retrieval_service import get_rag_service

async def test():
    rag = get_rag_service()
    chunks = await rag.retrieve("კანაფის ფისის ნარკოტიკის ზღვრები რაარის")
    print("Top 5 chunks:")
    for c in chunks[:5]:
        meta = c.get("metadata", {})
        print(f"ID: {c['chunk_id']} | Dist: {c.get('distance')} | Src: {c.get('source')} | Type: {meta.get('chunk_type')}")

asyncio.run(test())
