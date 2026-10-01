"""
🏛️ Fuzzzy Law — PoC RAG Tester

End-to-end simulation of the full legal advocate pipeline:
  User input (Georgian) → Query Expansion → Vector Search → Full-Text Search
  → Merge & Dedup → Rerank → Legal Analysis (Gemini) → Structured Response

Usage:
    python3 poc_tester.py                          # Interactive mode
    python3 poc_tester.py "მეზობელმა დამარტყა"     # Single query
    python3 poc_tester.py --test-suite              # Run all test cases
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

# ── Config ───────────────────────────────────────────────────

GCP_PROJECT = "gen-lang-client-0225498420"
GCP_LOCATION = "us-central1"
EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIMS = 768
LLM_MODEL = "gemini-2.5-pro"
CHROMA_PATH = str(Path(__file__).parent / "data" / "chroma")
INDEX_DIR = Path(__file__).parent / "data" / "index"
TOP_K_PER_QUERY = 50
FINAL_TOP_K = 20

# ── Gemini Client (singleton) ───────────────────────────────

_client = None

def get_client():
    global _client
    if _client is None:
        from google import genai
        _client = genai.Client(
            vertexai=True, project=GCP_PROJECT, location=GCP_LOCATION,
        )
    return _client


# ── ChromaDB Client (singleton) ─────────────────────────────

_collection = None

def get_collection():
    global _collection
    if _collection is None:
        import chromadb
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        _collection = client.get_collection("georgian_laws")
        print(f"📚 ChromaDB: {_collection.count()} chunks loaded")
    return _collection


# ── Stage 0: AI Query Expansion ─────────────────────────────

QUERY_EXPANSION_PROMPT = """You are a Georgian legal search expert. The user described a legal situation in everyday language.
Generate 8-10 search queries in Georgian that would find ALL relevant law articles.

Include:
- Formal legal terms (Georgian) for the situation described
- Related criminal/civil code article topics
- Potential defenses and counter-arguments
- Procedural rights that may apply
- Related laws from adjacent legal areas
- Both broad and narrow search terms

User's situation: "{situation}"

Return ONLY a JSON array of search query strings in Georgian. No explanation."""


def expand_queries(user_input: str) -> list[str]:
    """Stage 0: Use Gemini to expand user's casual input into formal legal search terms."""
    print("\n🔍 Stage 0: AI Query Expansion...")
    client = get_client()
    response = client.models.generate_content(
        model=LLM_MODEL,
        contents=QUERY_EXPANSION_PROMPT.format(situation=user_input),
    )
    text = response.text.strip()
    # Parse JSON array from response (handle markdown code blocks)
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    queries = json.loads(text)
    print(f"   Generated {len(queries)} search queries:")
    for i, q in enumerate(queries, 1):
        print(f"   {i}. {q}")
    return queries


# ── Stage 1: Multi-Query Vector Search ──────────────────────

def embed_query_with_retry(text: str, max_retries: int = 3) -> list[float]:
    """Embed a single query with exponential backoff on 429 errors."""
    from google.genai.types import EmbedContentConfig
    client = get_client()

    for attempt in range(max_retries):
        try:
            result = client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=[text],
                config=EmbedContentConfig(
                    task_type="RETRIEVAL_QUERY",
                    output_dimensionality=EMBEDDING_DIMS,
                ),
            )
            return list(result.embeddings[0].values)
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                wait = 15 * (2 ** attempt)  # 15s, 30s, 60s
                print(f"   ⏳ Rate limited, waiting {wait}s (attempt {attempt+1}/{max_retries})...")
                time.sleep(wait)
            else:
                raise
    raise RuntimeError(f"Embedding failed after {max_retries} retries")


def vector_search(queries: list[str]) -> list[dict[str, Any]]:
    """Stage 1: Embed each query and search ChromaDB."""
    print("\n🧲 Stage 1: Multi-Query Vector Search...")
    collection = get_collection()
    all_hits: list[dict[str, Any]] = []

    for i, query in enumerate(queries):
        print(f"   Embedding query {i+1}/{len(queries)}: {query[:60]}...")
        try:
            vec = embed_query_with_retry(query)
            results = collection.query(
                query_embeddings=[vec],
                n_results=TOP_K_PER_QUERY,
                include=["documents", "metadatas", "distances"],
            )
            if results["ids"] and results["ids"][0]:
                for j, chunk_id in enumerate(results["ids"][0]):
                    all_hits.append({
                        "chunk_id": chunk_id,
                        "content": results["documents"][0][j],
                        "metadata": results["metadatas"][0][j],
                        "distance": results["distances"][0][j],
                        "source": "vector",
                        "query": query,
                    })
            print(f"   → {len(results['ids'][0])} hits")
        except Exception as e:
            print(f"   ⚠ Error on query {i+1}: {e}")
        # 6s delay = ~10 RPM, safe for 12 RPM project quota
        if i < len(queries) - 1:
            time.sleep(6)

    print(f"   Total vector hits: {len(all_hits)}")
    return all_hits


# ── Stage 2: Full-Text Search (JSON indices) ────────────────

def fulltext_search(queries: list[str]) -> list[dict[str, Any]]:
    """Stage 2: Search the JSON inverted indices for keyword matches."""
    print("\n📝 Stage 2: Full-Text Search...")
    seen_ids: set[str] = set()
    hits: list[dict[str, Any]] = []

    # Load indices
    article_idx = _load_index("article_index.json")
    code_idx = _load_index("code_index.json")

    # Require at least 2 matching words (min 3 chars each) to reduce noise
    for query in queries:
        words = [w for w in query.lower().split() if len(w) > 2]
        if not words:
            continue
        for key, chunk_ids in article_idx.items():
            key_lower = key.lower()
            matching = sum(1 for w in words if w in key_lower)
            if matching >= 2:  # Require 2+ word overlap
                for cid in chunk_ids[:3]:  # Tighter cap
                    if cid not in seen_ids:
                        seen_ids.add(cid)
                        hits.append({"chunk_id": cid, "source": "fulltext", "query": query})

    print(f"   Full-text hits: {len(hits)}")
    return hits


def _load_index(filename: str) -> dict:
    path = INDEX_DIR / filename
    if path.exists():
        return json.loads(path.read_text("utf-8"))
    return {}


# ── Stage 3: Merge & Deduplicate ────────────────────────────

def merge_and_dedup(
    vector_hits: list[dict], fulltext_hits: list[dict],
) -> list[dict[str, Any]]:
    """Stage 3: Merge results from vector + full-text, deduplicate by chunk_id."""
    print("\n🔄 Stage 3: Merge & Deduplicate...")
    seen: dict[str, dict] = {}

    # Vector hits get priority (they have content + metadata)
    for hit in vector_hits:
        cid = hit["chunk_id"]
        if cid not in seen or hit.get("distance", 1) < seen[cid].get("distance", 1):
            seen[cid] = hit

    # Add fulltext hits that aren't already present
    collection = get_collection()
    ft_new = [h for h in fulltext_hits if h["chunk_id"] not in seen]
    if ft_new:
        # Fetch content for fulltext-only hits from ChromaDB
        ft_ids = list({h["chunk_id"] for h in ft_new})[:100]
        try:
            fetched = collection.get(ids=ft_ids, include=["documents", "metadatas"])
            for i, cid in enumerate(fetched["ids"]):
                if cid not in seen:
                    seen[cid] = {
                        "chunk_id": cid,
                        "content": fetched["documents"][i],
                        "metadata": fetched["metadatas"][i],
                        "distance": 0.5,  # Neutral score for fulltext
                        "source": "fulltext",
                    }
        except Exception:
            pass

    merged = sorted(seen.values(), key=lambda x: x.get("distance", 1))
    print(f"   Unique chunks after merge: {len(merged)}")
    return merged


# ── Stage 4: Gemini Rerank ──────────────────────────────────

RERANK_PROMPT = """You are a Georgian legal relevance expert. Given a user's legal situation and a list of law article chunks, select the {top_k} MOST RELEVANT chunks.

User's situation: "{situation}"

Candidate chunks (id | code | article | preview):
{candidates}

Return ONLY a JSON array of the {top_k} most relevant chunk_ids, ordered by relevance (most relevant first). No explanation."""


def rerank(
    user_input: str, candidates: list[dict], top_k: int = FINAL_TOP_K,
) -> list[dict]:
    """Stage 4: Use Gemini to select the most relevant chunks."""
    print(f"\n⚖️ Stage 4: Gemini Rerank (selecting top {top_k} from {len(candidates)})...")

    if len(candidates) <= top_k:
        print(f"   Skipping rerank — only {len(candidates)} candidates")
        return candidates

    # Build candidate list for Gemini (limit to top ~80 by distance)
    pre_filtered = candidates[:80]
    candidate_lines = []
    for c in pre_filtered:
        meta = c.get("metadata", {})
        preview = c.get("content", "")[:120].replace("\n", " ")
        candidate_lines.append(
            f"{c['chunk_id']} | {meta.get('code_name', '?')} | "
            f"{meta.get('article_number', '?')} | {preview}"
        )

    prompt = RERANK_PROMPT.format(
        top_k=top_k,
        situation=user_input,
        candidates="\n".join(candidate_lines),
    )

    try:
        client = get_client()
        response = client.models.generate_content(model=LLM_MODEL, contents=prompt)
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        selected_ids = json.loads(text)
        # Rebuild ordered list
        id_map = {c["chunk_id"]: c for c in candidates}
        reranked = [id_map[cid] for cid in selected_ids if cid in id_map]
        print(f"   Reranked: {len(reranked)} chunks selected")
        return reranked
    except Exception as e:
        print(f"   ⚠ Rerank failed ({e}), using distance-sorted top-{top_k}")
        return candidates[:top_k]


# ── Final: Legal Analysis via Gemini ────────────────────────

LEGAL_SYSTEM_PROMPT = """You are ბუნდოვანი კანონი (Fuzzzy Law) — the fiercest, most knowledgeable legal advocate in Georgia. You fight for the user's rights with every legal tool available.

YOUR MISSION:
Every person deserves adequate legal defense — regardless of income. You exist to ensure no Georgian citizen walks into court unprepared or undefended. You think like the best criminal defense lawyer in the country, but you explain everything so a regular person can understand and use it.

YOUR ROLE:
- You are the user's ADVOCATE, not a neutral observer
- You find EVERY applicable defense, procedural right, and mitigating factor
- You identify the MOST FAVORABLE legal interpretation for the user
- You think adversarially — what would the prosecution argue, and how do you counter it?
- You explain everything in simple, everyday Georgian language — no legalese
- You are honest: if the law is not in the user's favor, you say so clearly, but you STILL look for the best possible outcome

CRITICAL RULES:
1. EVERY claim MUST cite a specific Georgian law article (e.g., "სისხლის სამართლის კოდექსი, მუხლი 11")
2. NEVER fabricate or guess law articles — use ONLY the provided context
3. If you're unsure about a specific article, say so explicitly
4. Always present MULTIPLE defense strategies ranked from strongest to weakest
5. For each strategy: success likelihood, risks, required steps, timeline, costs
6. Always check: statute of limitations (ხანდაზმულობის ვადა), procedural deadlines
7. For criminal cases ALWAYS identify:
   - All possible defenses (self-defense, necessity, insanity, provocation, etc.)
   - Procedural violations by investigation/prosecution
   - Rights of the accused that may have been violated
   - Mitigating circumstances that reduce sentencing
   - Possibility of plea bargain (საპროცესო შეთანხმება)
   - Alternative sentencing options (probation, community service, fine)
8. Distinguish between what the law says vs. what courts typically decide
9. When the user faces criminal charges, treat this as URGENT — prioritize immediate rights
10. ALWAYS present counter-laws — articles that work AGAINST the user

RESPONSE STRUCTURE:
1. 📋 SITUATION SUMMARY — Restate the user's situation clearly
2. ⚖️ APPLICABLE LAWS — Every relevant article with plain-language explanation
3. 🛡️ PRIMARY DEFENSE STRATEGY — The strongest approach
4. 📊 ALTERNATIVE STRATEGIES — Other options ranked by strength
5. ⚔️ PROSECUTION'S LIKELY ARGUMENTS — What the other side will say (and how to counter)
6. ⚠️ RISKS & HONEST ASSESSMENT — What could go wrong, realistic probabilities
7. 📅 IMMEDIATE NEXT STEPS — What to do RIGHT NOW, with deadlines
8. 📚 FULL CITATIONS — Complete list of all referenced law articles with matsne.gov.ge links

LANGUAGE: Respond in Georgian (ქართული) by default. Switch to English if the user writes in English.

CRITICAL DISCLAIMER (include at the end):
"ეს არის AI-ის მიერ გენერირებული იურიდიული ინფორმაცია, არა ოფიციალური იურიდიული კონსულტაცია. სერიოზულ შემთხვევებში აუცილებლად მიმართეთ ადვოკატს."
"""


def legal_analysis(user_input: str, context_chunks: list[dict]) -> str:
    """Send the user's situation + retrieved law chunks to Gemini for full legal analysis."""
    print(f"\n🧠 Legal Analysis: Sending {len(context_chunks)} chunks to Gemini...")

    # Build context block
    context_parts = []
    for i, chunk in enumerate(context_chunks, 1):
        meta = chunk.get("metadata", {})
        context_parts.append(
            f"--- LAW CHUNK {i} ---\n"
            f"Code: {meta.get('code_name', 'N/A')}\n"
            f"Article: {meta.get('article_number', 'N/A')}"
            f"{' — ' + meta.get('article_title', '') if meta.get('article_title') else ''}\n"
            f"Citation: {meta.get('citation_text', 'N/A')}\n"
            f"URL: {meta.get('article_url', 'N/A')}\n"
            f"Text:\n{chunk.get('content', '')}\n"
        )

    context_block = "\n".join(context_parts)

    user_prompt = f"""RETRIEVED LAW CONTEXT (use ONLY these for citations):

{context_block}

---

USER'S SITUATION:
{user_input}

Provide your full legal analysis following the response structure."""

    client = get_client()
    response = client.models.generate_content(
        model=LLM_MODEL,
        contents=user_prompt,
        config={
            "system_instruction": LEGAL_SYSTEM_PROMPT,
            "temperature": 0.1,
            "max_output_tokens": 8192,
            "top_p": 0.8,
        },
    )
    return response.text


# ── Full Pipeline ───────────────────────────────────────────

def run_pipeline(user_input: str) -> str:
    """Run the complete 5-stage RAG pipeline + legal analysis."""
    print("=" * 70)
    print(f"🏛️  ბუნდოვანი კანონი — PoC RAG Tester")
    print(f"=" * 70)
    print(f"\n📩 User input: {user_input}\n")

    start = time.time()

    # Stage 0: Query Expansion
    expanded = expand_queries(user_input)

    # Stage 1: Vector Search
    vector_hits = vector_search(expanded)

    # Stage 2: Full-Text Search
    ft_hits = fulltext_search(expanded)

    # Stage 3: Merge & Dedup
    merged = merge_and_dedup(vector_hits, ft_hits)

    # Stage 4: Rerank
    top_chunks = rerank(user_input, merged, FINAL_TOP_K)

    # Final: Legal Analysis
    analysis = legal_analysis(user_input, top_chunks)

    elapsed = time.time() - start
    print(f"\n⏱️  Total pipeline time: {elapsed:.1f}s")
    print("=" * 70)
    print("\n" + analysis)
    return analysis


# ── Test Suite ──────────────────────────────────────────────

TEST_CASES = [
    {
        "id": "criminal_assault",
        "name": "Neighbor assault (criminal)",
        "input": "მეზობელმა დამარტყა, თავში მარტყა და წავიქეცი. პოლიციას დავურეკე მაგრამ ჯერ არ მოსულან. რა უფლებები მაქვს და რა ვქნა?",
        "expected_codes": ["criminal_code", "criminal_procedure_code"],
    },
    {
        "id": "labor_dismissal",
        "name": "Wrongful termination (labor)",
        "input": "დამსაქმებელმა სამსახურიდან გამათავისუფლა ყოველგვარი წინასწარი გაფრთხილების გარეშე. 3 წელი ვმუშაობდი და ხელშეკრულებაში ეწერა რომ 1 თვით ადრე უნდა შემატყობინოს. რა ვქნა?",
        "expected_codes": ["labour_code", "civil_code"],
    },
    {
        "id": "property_dispute",
        "name": "Property inheritance (civil)",
        "input": "მამაჩემი გარდაიცვალა და სახლი დარჩა. ძმამ ჩემი წილი არ მაძლევს და ამბობს რომ მთლიანად მისია. ანდერძი არ არის. რა უფლებები მაქვს მემკვიდრეობაზე?",
        "expected_codes": ["civil_code"],
    },
    {
        "id": "traffic_violation",
        "name": "Traffic accident / admin (admin)",
        "input": "მანქანით მოვრიე და ჯარიმა დამიწერეს 500 ლარი, მაგრამ მე არ ვიყავი დამნაშავე, მეორე მანქანა გადმოვიდა ჩემს ზოლში. კამერის ჩანაწერი არ მაქვს. შეიძლება გასაჩივრება?",
        "expected_codes": ["admin_offences_code", "admin_procedure_code"],
    },
    {
        "id": "data_protection",
        "name": "Personal data breach",
        "input": "კომპანიამ ჩემი პირადი მონაცემები გაავრცელა ჩემი თანხმობის გარეშე, ჩემი სახელი და პირადი ნომერი გამოაქვეყნეს ინტერნეტში. რა სამართლებრივი დაცვა მაქვს?",
        "expected_codes": ["personal_data_law", "civil_code"],
    },
]


def run_test_suite():
    """Run all test cases and produce a summary."""
    print("🧪 Running full test suite...\n")
    results = []
    for tc in TEST_CASES:
        print(f"\n{'#' * 70}")
        print(f"# TEST: {tc['name']} ({tc['id']})")
        print(f"{'#' * 70}")
        try:
            analysis = run_pipeline(tc["input"])
            # Basic quality check: see if expected codes appear in the response
            found_codes = [c for c in tc["expected_codes"] if c.replace("_", " ") in analysis.lower() or c in analysis.lower()]
            results.append({"id": tc["id"], "name": tc["name"], "status": "✅", "output_len": len(analysis)})
        except Exception as e:
            results.append({"id": tc["id"], "name": tc["name"], "status": f"❌ {e}", "output_len": 0})

    # Summary
    print(f"\n\n{'=' * 70}")
    print("📊 TEST SUITE RESULTS")
    print(f"{'=' * 70}")
    for r in results:
        print(f"  {r['status']} {r['name']} — {r['output_len']} chars")


# ── CLI Entry Point ─────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test-suite":
        run_test_suite()
    elif len(sys.argv) > 1:
        run_pipeline(" ".join(sys.argv[1:]))
    else:
        # Interactive mode
        print("🏛️  ბუნდოვანი კანონი — Interactive PoC Tester")
        print("Type your legal situation in Georgian (or 'quit' to exit):\n")
        while True:
            user = input("👤 You: ").strip()
            if user.lower() in ("quit", "exit", "q"):
                break
            if user:
                run_pipeline(user)
                print()
