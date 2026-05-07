"""
Court Practice module — Supreme Court decisions (2022-2026).

These are interpretive, non-binding decisions that show how the Supreme Court
applies and interprets Georgian law. Organized by category:
criminal, civil, and administrative.
"""

from modules import CorpusModule


class CourtPracticeModule(CorpusModule):
    """Supreme Court case law — interpretive, non-binding."""

    @property
    def id(self) -> str:
        return "court_practice"

    @property
    def name_ka(self) -> str:
        return "სასამართლო პრაქტიკა"

    @property
    def name_en(self) -> str:
        return "Supreme Court Practice"

    @property
    def description(self) -> str:
        return (
            "Supreme Court decisions (2022-2026) covering criminal, civil, "
            "and administrative cases. Shows how courts interpret and apply "
            "Georgian legislation in real cases."
        )

    @property
    def enabled_by_default(self) -> bool:
        return False

    @property
    def rag_instructions(self) -> str:
        return """
When citing retrieved COURT PRACTICE (სასამართლო პრაქტიკა) chunks:
- Always cite the full case number (e.g., "ბს-245-242(კ-24)")
- Specify the case category: criminal (სისხლი), civil (სამოქალაქო),
  or administrative (ადმინისტრაციული)
- Note the decision year — more recent decisions carry more weight
- These are INTERPRETIVE — they show how courts APPLY the law in practice
- They are NOT formally binding precedent (unlike Grand Chamber decisions)
- Use them to strengthen arguments:
  • "სასამართლო პრაქტიკის მიხედვით..." (According to court practice...)
  • "უზენაესმა სასამართლომ განმარტა, რომ..." (The Supreme Court interpreted that...)
- If a court interpretation differs from the literal statutory text,
  present BOTH the textual meaning and the judicial interpretation
- When multiple court decisions address the same issue, note whether
  the practice is consistent or evolving
- Always connect court practice back to the specific law articles being interpreted
"""
