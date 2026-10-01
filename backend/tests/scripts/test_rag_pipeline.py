import asyncio
from app.services.rag_retrieval_service import get_rag_service

async def main():
    rag = get_rag_service()
    chunks = await rag.retrieve("კანაფის ფისის ნარკოტიკის ზღვრები რაარის", collections=["georgian_laws"])
    for i, c in enumerate(chunks[:5]):
        print(f"[{i}] {c.get('chunk_id')} | {c.get('metadata', {}).get('chunk_type', '')}")
        print(c.get('content', '')[:200])
        print("-" * 40)

if __name__ == "__main__":
    asyncio.run(main())
