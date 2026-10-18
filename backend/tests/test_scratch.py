import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
import uuid
from app.models.database import Base
from sqlalchemy.orm.attributes import flag_modified

class TestModel(Base):
    __tablename__ = "test_model"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    data = Column(JSONB, nullable=True)

async def test_flag():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with SessionLocal() as session:
        obj = TestModel(id=uuid.uuid4(), data={"a": 1})
        session.add(obj)
        await session.commit()
        
        # Now update
        obj.data = {"a": 2}
        flag_modified(obj, "data")
        await session.commit()
        print("Success!")

if __name__ == "__main__":
    asyncio.run(test_flag())
