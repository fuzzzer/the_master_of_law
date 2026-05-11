import asyncio
import sys
import os

# Add the parent directory to sys.path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models.database import Base, get_engine
from app.models import conversation, user, feedback, case_file, message, questionnaire, user_credits

async def init():
    print("Initializing database tables...")
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print('All tables created successfully!')

if __name__ == "__main__":
    asyncio.run(init())
