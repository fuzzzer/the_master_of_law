import json
from pathlib import Path
from typing import Any

from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ThresholdService:
    """Dedicated service for exact/heuristic lookups of legal thresholds.

    Bypasses vector search to guarantee precise retrieval of tables and numbers.
    """

    def __init__(self) -> None:
        self._catalog: list[dict[str, Any]] = []
        self._load_catalog()

    def _load_catalog(self) -> None:
        path = (
            Path(settings.chroma_persist_dir).parent
            / "thresholds"
            / "threshold_catalog.json"
        )
        if not path.exists():
            logger.warning("threshold_catalog_not_found", path=str(path))
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._catalog = data.get("thresholds", [])
        except Exception as e:
            logger.error("failed_to_load_threshold_catalog", error=str(e))

    def search(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        """Search the threshold catalog using basic Georgian text matching."""
        if not self._catalog:
            return []

        tokens = [t for t in query.lower().split() if len(t) >= 3]
        if not tokens:
            return []

        hits: list[tuple[float, dict[str, Any]]] = []
        for entry in self._catalog:
            text = json.dumps(entry, ensure_ascii=False).lower()
            score = 0.0
            for t in tokens:
                if t in text:
                    score += 1.0
                elif len(t) >= 5 and t[:4] in text:
                    score += 0.8
            if score > 0:
                hits.append((score, entry))

        hits.sort(key=lambda x: x[0], reverse=True)

        results = []
        for _, entry in hits[:top_k]:
            results.append(
                {
                    "chunk_id": f"threshold_{entry['id']}",
                    "content": self._format_entry(entry),
                    "metadata": {
                        "chunk_type": "threshold",
                        "_collection": "georgian_laws",
                        "code_name": entry.get("code_name", "Unknown"),
                        "article_number": entry.get("article_number", "Unknown"),
                    },
                    "distance": 0.0,  # Exact matches
                    "source": "lookup",
                }
            )
        return results

    def _format_entry(self, entry: dict[str, Any]) -> str:
        parts = [
            f"[იურიდიული ზღვარი / Legal Threshold]",
            f"კოდექსი: {entry.get('code_name', '')}",
            f"მუხლი: {entry.get('article_number', '')}",
            f"აღწერა: {entry.get('description_ka', '')}",
        ]
        if entry.get("substance"):
            parts.append(f"ნივთიერება: {entry['substance']}")

        parts.append("ზღვრები:")
        for key, value in entry.get("values", {}).items():
            parts.append(f"  • {key}: {value}")

        if entry.get("consequence_ka"):
            parts.append(f"შედეგი: {entry['consequence_ka']}")

        return "\n".join(parts)


_threshold_service: ThresholdService | None = None


def get_threshold_service() -> ThresholdService:
    global _threshold_service
    if _threshold_service is None:
        _threshold_service = ThresholdService()
    return _threshold_service
