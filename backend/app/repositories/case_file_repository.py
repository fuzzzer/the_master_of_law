"""
Case file repository — CRUD for case_files table.
"""

from __future__ import annotations

import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case_file import CaseFile
from app.utils.logger import get_logger

logger = get_logger(__name__)


class CaseFileRepository:
    """Data access layer for defense case files."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, **kwargs) -> CaseFile:
        """Create a new case file."""
        cf = CaseFile(id=uuid.uuid4(), **kwargs)
        self._db.add(cf)
        await self._db.flush()
        logger.info("case_file_created", id=str(cf.id))
        return cf

    async def get_by_id(self, case_file_id: uuid.UUID) -> CaseFile | None:
        stmt = select(CaseFile).where(CaseFile.id == case_file_id)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_user(self, user_id: str, limit: int = 50) -> list[CaseFile]:
        stmt = (
            select(CaseFile)
            .where(CaseFile.user_id == user_id)
            .order_by(CaseFile.updated_at.desc())
            .limit(limit)
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def count_for_user(self, user_id: str) -> int:
        from sqlalchemy import func
        stmt = select(func.count()).select_from(CaseFile).where(CaseFile.user_id == user_id)
        result = await self._db.execute(stmt)
        return result.scalar_one()

    async def update(self, case_file_id: uuid.UUID, **kwargs) -> CaseFile | None:
        cf = await self.get_by_id(case_file_id)
        if not cf:
            return None
        
        from sqlalchemy.orm.attributes import flag_modified
        json_columns = {
            "facts", "evidence", "applicable_laws", "defense_strategies", 
            "prosecution_args", "action_checklist", "unclear_items", 
            "lawyer_brief", "citations", "retrieved_chunks"
        }
        
        for k, v in kwargs.items():
            if hasattr(cf, k) and v is not None:
                setattr(cf, k, v)
                if k in json_columns:
                    flag_modified(cf, k)
                    
        await self._db.flush()
        return cf

    async def delete(self, case_file_id: uuid.UUID) -> bool:
        stmt = delete(CaseFile).where(CaseFile.id == case_file_id)
        result = await self._db.execute(stmt)
        await self._db.flush()
        return result.rowcount > 0
