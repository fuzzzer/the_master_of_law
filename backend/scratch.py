import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer
from sqlalchemy.dialects.postgresql import JSONB, UUID
from app.models.database import Base
from app.models.case_file import CaseFile
from sqlalchemy.orm.attributes import flag_modified
import uuid

async def test():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as session:
        cf = CaseFile(id=uuid.uuid4(), user_id="test_user", title="test")
        session.add(cf)
        await session.commit()
        
        cf.facts = {"a": 1}
        flag_modified(cf, "facts")
        await session.commit()
        print("Success")

asyncio.run(test())
