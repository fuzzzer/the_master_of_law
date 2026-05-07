"""
Georgian Laws module — current consolidated legal codes from matsne.gov.ge.

This is the primary knowledge source. Always enabled by default.
The existing law_corpus pipeline (scrape → parse → chunk → embed → index)
populates this module's ChromaDB collection.
"""

from modules import CorpusModule


class GeorgianLawsModule(CorpusModule):
    """Current consolidated Georgian legislation from Matsne."""

    @property
    def id(self) -> str:
        return "georgian_laws"

    @property
    def name_ka(self) -> str:
        return "კანონმდებლობა"

    @property
    def name_en(self) -> str:
        return "Georgian Legislation"

    @property
    def description(self) -> str:
        return (
            "Current consolidated legal codes from matsne.gov.ge — "
            "15 codes, 9,450+ chunks. Includes: Constitution, Criminal Code, "
            "Civil Code, Administrative Code, Tax Code, and more."
        )

    @property
    def enabled_by_default(self) -> bool:
        return True

    @property
    def rag_instructions(self) -> str:
        return """
When citing retrieved LEGISLATION (კანონმდებლობა) chunks:
- Always cite the specific code name and article number
  (e.g., "სამოქალაქო კოდექსი, მუხლი 45")
- Link to the Matsne URL if available in chunk metadata
- These are CURRENT CONSOLIDATED texts — they represent active, enforceable law
- Distinguish between:
  • Imperative norms (mandatory — "ვალდებულია", "უნდა")
  • Permissive norms (optional — "უფლება აქვს", "შეუძლია")
  • Prohibitive norms ("ეკრძალება", "არ შეიძლება")
- When multiple articles apply, present them in order of specificity
  (specific provision overrides general provision — lex specialis)
- Note the structural hierarchy: Code → Book → Part → Chapter → Article → Paragraph
"""
