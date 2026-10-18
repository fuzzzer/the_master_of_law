"""
RAG pipeline prompts — query expansion and reranking.
"""

from app.prompts import PromptRole, PromptTemplate


QUERY_EXPANSION = PromptTemplate(
    name="rag_query_expansion",
    role=PromptRole.USER,
    template=(
        "You are a Georgian legal search expert. The user described a situation.\n"
        "First, analyze the user's message and determine if searching the legal database is necessary.\n"
        "If the message is a simple greeting, a non-legal question, or a statement that doesn't require "
        "new legal context, return an empty JSON array: []\n\n"
        "If a legal search IS needed, generate {count} search queries in Georgian that would find ALL relevant law articles.\n\n"
        "Include:\n"
        "- Formal legal terms for the situation described\n"
        "- Related criminal/civil code article topics\n"
        "- Potential defenses and counter-arguments\n"
        "- Procedural rights that may apply\n"
        "- Related laws from adjacent legal areas\n"
        "- Both broad and narrow search terms\n\n"
        'User\'s message: "{user_message}"\n\n'
        "Return ONLY a JSON array of search query strings in Georgian. If no search is needed, return []."
    ),
    description="Expands a user's legal question into formal search queries, or returns empty if search is unnecessary.",
    variables=("count", "user_message"),
    temperature=0.3,
    response_format="json",
)


RERANK = PromptTemplate(
    name="rag_rerank",
    role=PromptRole.USER,
    template=(
        "You are a Georgian legal expert. Given the user's legal situation "
        "and candidate law chunks, select the {top_k} MOST RELEVANT chunks.\n\n"
        "USER'S SITUATION:\n{user_message}\n\n"
        "CANDIDATE LAW CHUNKS:\n{chunks_json}\n\n"
        "Return ONLY a JSON array of the selected chunk_id strings, nothing else."
    ),
    description="Selects the most relevant law chunks from a merged candidate set.",
    variables=("top_k", "user_message", "chunks_json"),
    temperature=0.1,
    response_format="json",
)
