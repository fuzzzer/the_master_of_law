# User Notes — Law Corpus Audit

## Priority: HIGH

This directly affects whether users get correct legal information. A wrong article reference can lead someone to the wrong law.

## Key Issues Found (from live data audit, 2026-05-24)

1. **20 chunks have wrong code names** — metadata search fails for these articles. If someone asks about `მუხლი 177` (theft) and the system searches by `code_name="საქართველოს სისხლის სამართლის კოდექსი"`, it won't find the 15 chunks stored under `სისხლის სამართლის კოდექსი` (without prefix).

2. **Grand Chamber binding rules missing** — These are the most powerful legal precedents. The system tells the AI "Grand Chamber decisions are BINDING" but can't tell it *what the binding rule actually is* because the metadata is empty.

3. **No article cross-references in court practice** — Court rulings cite specific law articles (e.g. `სსკ-ის 177-ე მუხლის მე-2 ნაწილის`), but this isn't in metadata. The system can't say "this court case is about theft (მუხლი 177)."

## Out of Scope

- Re-embedding chunks (embeddings are fine, metadata is the problem)
- Adding new collections
- Changing the RAG pipeline itself
