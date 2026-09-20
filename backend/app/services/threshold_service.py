import json
import re
from pathlib import Path
from typing import Any

from app.config.settings import settings
from app.services.trace_service import record_step
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Maps each catalog code_name to the legal domain its thresholds belong to
# (keys from legal_classifier_service.LEGAL_DOMAINS). Entries whose domain
# does not match the query's classified domain are not injected.
# Minimum topical-match score before an entry may be injected — at least two
# strong token hits on the entry's own description/substance/code fields.
_MIN_MATCH_SCORE = 1.8

_CODE_NAME_TO_DOMAIN: dict[str, str] = {
    "ნარკოტიკული საშუალებების შესახებ კანონი": "criminal",
    "სისხლის სამართლის კოდექსი": "criminal",
    "სისხლის სამართლის საპროცესო კოდექსი": "criminal",
    "სამოქალაქო კოდექსი": "civil",
    "ადმინისტრაციულ სამართალდარღვევათა კოდექსი": "administrative",
    "შრომის კოდექსი": "labor",
}


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

    def search(
        self,
        query: str,
        top_k: int = 3,
        query_domains: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Search the threshold catalog using basic Georgian text matching.

        Parameters
        ----------
        query : str
            The user's question.
        top_k : int
            Max entries to inject.
        query_domains : list[str] | None
            Legal domains the query was classified into. When given, entries
            from a different domain are gated out (None = no gating).
        """
        if not self._catalog:
            return []

        tokens = [t for t in query.lower().split() if len(t) >= 3]
        if not tokens:
            return []

        hits: list[tuple[float, dict[str, Any]]] = []
        gated_out: list[str] = []
        for entry in self._catalog:
            entry_domain = _CODE_NAME_TO_DOMAIN.get(entry.get("code_name", ""))
            # Score only against the entry's meaningful fields — matching the
            # whole JSON (values/consequences boilerplate) let unrelated
            # entries slip into prompts on generic-token hits.
            text = " ".join([
                entry.get("description_ka", ""),
                entry.get("substance") or "",
                entry.get("code_name", ""),
                entry.get("article_number", ""),
                entry.get("threshold_type", ""),
            ]).lower()
            score = 0.0
            for t in tokens:
                if t in text:
                    score += 1.0
                elif len(t) >= 5 and t[:5] in text:
                    score += 0.8
            # a direct hit on the substance name (drug entries) is specific
            # enough on its own — "მარიხუანა" alone must find its threshold.
            # Word-level comparison: substring matching let short common words
            # ("არა") hit inside long chemical names.
            substance = (entry.get("substance") or "").lower()
            substance_words = {
                w for w in re.split(r"[\s,()\-–]+", substance) if len(w) >= 4
            }
            substance_hit = any(
                qt == w or (len(qt) >= 5 and w.startswith(qt[:5]))
                for w in substance_words
                for qt in tokens
                if len(qt) >= 4
            )
            if score < _MIN_MATCH_SCORE and not substance_hit:
                continue
            if substance_hit:
                score += 2.0
            if (
                query_domains is not None
                and entry_domain is not None
                and entry_domain not in query_domains
            ):
                gated_out.append(entry["id"])
                continue
            hits.append((score, entry))

        hits.sort(key=lambda x: x[0], reverse=True)

        record_step(
            "threshold_lookup",
            query_domains=query_domains,
            injected=[entry["id"] for _, entry in hits[:top_k]],
            gated_out_by_domain=gated_out[:20],
            gated_out_count=len(gated_out),
        )

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
                        "article_url": entry.get("source_url", ""),
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

        if entry.get("source_url"):
            parts.append(f"წყარო (URL for citation): {entry['source_url']}")

        return "\n".join(parts)


_threshold_service: ThresholdService | None = None


def get_threshold_service() -> ThresholdService:
    global _threshold_service
    if _threshold_service is None:
        _threshold_service = ThresholdService()
    return _threshold_service
