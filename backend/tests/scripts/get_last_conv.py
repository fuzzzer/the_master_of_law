import asyncio
from sqlalchemy import select
from app.models.database import get_session_factory
from app.models.conversation import Conversation
from app.models.message import Message

async def main():
    async with get_session_factory()() as db:
        # Get latest conversation with messages
        result = await db.execute(select(Conversation).order_by(Conversation.created_at.desc()).limit(2))
        convs = result.scalars().all()
        for conv in convs:
            print(f"Conv: {conv.id} - {conv.title}")
            res = await db.execute(select(Message).where(Message.conversation_id == conv.id).order_by(Message.created_at.asc()))
            msgs = res.scalars().all()
            for m in msgs[-4:]: # Last 4 messages
                print(f"[{m.role.upper()}]: {m.content[:200]}...")
            print("-" * 40)

asyncio.run(main())
