"""
Grand Chamber module — binding norm interpretations.

Grand Chamber (დიდი პალატა) decisions carry the highest judicial authority
in Georgia. Their norm interpretations are BINDING on all lower courts.
"""

from modules import CorpusModule


class GrandChamberModule(CorpusModule):
    """Grand Chamber decisions — binding norm interpretations."""

    @property
    def id(self) -> str:
        return "grand_chamber"

    @property
    def name_ka(self) -> str:
        return "დიდი პალატა (სავალდებულო)"

    @property
    def name_en(self) -> str:
        return "Grand Chamber (Binding)"

    @property
    def description(self) -> str:
        return (
            "Grand Chamber decisions of the Supreme Court — binding norm "
            "interpretations that all lower courts must follow. Covers "
            "criminal, civil, and administrative law."
        )

    @property
    def enabled_by_default(self) -> bool:
        return False

    @property
    def rag_instructions(self) -> str:
        return """
When citing retrieved GRAND CHAMBER (დიდი პალატა) chunks:
- ⚠️ These are BINDING decisions — they override ALL lower court interpretations
- Always cite as: "დიდი პალატის გადაწყვეტილება, [case_number]"
- Grand Chamber decisions carry the HIGHEST judicial authority in Georgia
- If a Grand Chamber decision interprets a specific article of law,
  that interpretation IS the authoritative legal meaning for all courts
- Check chunk metadata for:
  • 'norm_interpreted' — which specific law article this decision binds
  • 'binding_rule' — the binding norm interpretation from the resolution
- If Grand Chamber contradicts regular court practice,
  Grand Chamber ALWAYS prevails — note this explicitly to the user
- Present the binding rule from the resolution (სარეზოლუციო) section
- When a Grand Chamber decision supports the user's position, emphasize
  its binding nature: "დიდი პალატის სავალდებულო განმარტებით..."
  (According to the Grand Chamber's binding interpretation...)
- When it works against the user, honestly acknowledge its binding force
  but look for distinguishing factors in the specific case
"""
