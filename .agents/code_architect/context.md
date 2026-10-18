# 🏗️ Code Architect — Skill Context

> **When to load:** Building new features, refactoring, adding endpoints, designing services.

---

## System Design Superpowers

### The "Onion" Test

Before adding ANY new abstraction, pass this test:

```
Layer 1 (Core):   Does the business logic work in a plain Python script?
Layer 2 (Infra):  Can I swap the database without touching business logic?
Layer 3 (API):    Can I swap REST for GraphQL without touching services?
Layer 4 (Deploy): Can I move from Docker to k8s without touching code?
```

If your code violates any layer boundary, you have a design problem — not a feature to add.

### Dependency Direction

```
Routes → Services → Repositories → Models
  ↓          ↓            ↓           ↓
HTTP      Business      Database    Schema
concerns   logic        queries     definition
```

**Dependencies flow INWARD only.** A service never imports a route. A repository never imports a service. Models import nothing from the app.

### The "Delete Test"

After writing a feature, ask: *"If I delete this file, what breaks?"*

- If deleting a route breaks a service → **coupling violation**
- If deleting a service breaks another service → **consider if one should call the other, not import it**
- If deleting a model breaks nothing → **dead code, delete it**

---

## Patterns for THIS Project

### Adding a New Endpoint (Checklist)

```
1. □ Create/update Pydantic schema in app/schemas/
2. □ Create/update repository method in app/repositories/
3. □ Create/update service method in app/services/
4. □ Create route handler in app/routes/ (max 15 lines)
5. □ Register router in app/main.py (if new file)
6. □ Add credit cost to config/constants.py (if applicable)
7. □ Add to CREDIT_ROUTES in middleware (if costs credits)
8. □ Write test in tests/
9. □ Update AI_GUIDE.md endpoint table
10. □ Test manually via curl
```

### Adding a New Service

```python
# Template: app/services/my_new_service.py

from app.utils.logger import get_logger

logger = get_logger(__name__)

class MyNewService:
    """One-line description of what this service does."""
    
    def __init__(self) -> None:
        """Initialize with any dependencies."""
        pass
    
    async def do_something(self, input_data: InputSchema) -> OutputSchema:
        """Verb-noun description.
        
        Args:
            input_data: What this parameter represents.
            
        Returns:
            What the caller gets back.
            
        Raises:
            SpecificError: When this specific thing goes wrong.
        """
        logger.info("doing_something", input_id=input_data.id)
        # ... implementation ...
        return result


# Singleton pattern (used throughout the project)
_service: MyNewService | None = None

def get_my_new_service() -> MyNewService:
    global _service
    if _service is None:
        _service = MyNewService()
    return _service
```

### Adding a New Repository

```python
# Template: app/repositories/my_repository.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.models.my_model import MyModel
from app.utils.logger import get_logger

logger = get_logger(__name__)

class MyRepository:
    """Data access layer for MyModel."""
    
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
    
    async def get_by_id(self, id: str) -> MyModel | None:
        """Fetch a single record by primary key."""
        result = await self.db.execute(
            select(MyModel).where(MyModel.id == id)
        )
        return result.scalar_one_or_none()
    
    async def create(self, **kwargs) -> MyModel:
        """Create and return a new record."""
        obj = MyModel(**kwargs)
        self.db.add(obj)
        await self.db.flush()
        return obj
```

---

## Anti-Patterns to Avoid

### 1. The "God Service"
```python
# ❌ BAD — one service that does everything
class LegalService:
    def search_laws(self): ...
    def analyze_case(self): ...
    def build_defense(self): ...
    def manage_credits(self): ...
    def authenticate_user(self): ...
```

```python
# ✅ GOOD — each service has ONE responsibility
class RagRetrievalService: ...    # Search and retrieve
class LegalAnalysisService: ...   # Analyze with Gemini
class CaseBuilderService: ...     # Build defense files
class CreditService: ...          # Manage credits
```

### 2. The "Leaky Abstraction"
```python
# ❌ BAD — route knows about SQLAlchemy
@router.get("/users/{id}")
async def get_user(id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == id))
    user = result.scalar_one_or_none()
    if user:
        credits = await db.execute(select(Credits).where(Credits.user_id == id))
        ...
```

```python
# ✅ GOOD — route calls service, service calls repo
@router.get("/users/{id}")
async def get_user(id: str, db: AsyncSession = Depends(get_db)):
    service = get_user_service()
    return await service.get_user_profile(id, db)
```

### 3. The "Stringly Typed" Trap
```python
# ❌ BAD — string literals scattered everywhere
if user.tier == "free":
    limit = 5
elif user.tier == "pro":
    limit = 30

# ✅ GOOD — enum/constant
from app.config.constants import UserTier, TIER_RATE_LIMITS

limit = TIER_RATE_LIMITS[user.tier]
```

### 4. The "Premature Abstraction"
```python
# ❌ BAD — AbstractFactoryBuilderPattern for 2 implementations
class VectorStoreFactory:
    @staticmethod
    def create(backend: str) -> AbstractVectorStore:
        if backend == "chroma":
            return ChromaVectorStore()
        elif backend == "pinecone":
            return PineconeVectorStore()
        # ... we'll never use Pinecone

# ✅ GOOD — just use ChromaDB directly
from app.integrations.chroma_client import get_chroma_client
```

---

## Performance Thinking

### The 3-Second Rule
Users expect legal analysis in <15 seconds. Budget:
- Query expansion: 1-2s
- Embedding: 0.5s (cached after first)
- Vector search: 0.1s (local ChromaDB)
- Full-text search: 0.05s
- Merge/dedup: 0.01s
- Rerank: 2-3s
- Gemini analysis: 5-8s (streaming)
- Citation verification: 0.1s
- **Total target: <12s**

### Where to Cache
1. **Query embeddings** — same question = same vector (TTL: 1 hour)
2. **ChromaDB results** — hot queries get cached (TTL: 30 min)
3. **Gemini rerank** — same chunk set = same ranking (TTL: 30 min)
4. **Law corpus metadata** — article_index.json loads once, stays in memory

### Where NOT to Cache
1. **Gemini analysis** — each conversation has unique context
2. **User credits** — must be real-time accurate
3. **Auth tokens** — security-critical, always verify
