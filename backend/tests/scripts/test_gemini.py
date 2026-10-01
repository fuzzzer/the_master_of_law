import asyncio
from app.integrations.vertex_ai_client import get_vertex_ai_client

async def main():
    try:
        client = get_vertex_ai_client()
        result = await client.generate("Say hello")
        print("Success:", result)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(main())
