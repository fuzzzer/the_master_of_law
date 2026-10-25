"""Deterministic scorecard checks (no AI). Pure functions over one answer text plus the item's expectations.

Checks:
  empty_or_broken     no answer, an error status, or under 40 characters of text
  citations           every cited article, looked up in the article store: exists / nonexistent / repealed /
                      paragraph_missing / other_law / unknown_code (same rules as the 2026-10-24 checker)
  required_articles   each any-of group in expected.required_articles is cited
  required_numbers    each named deadline/amount pattern appears in the answer
  forbidden_patterns  expected.must_not_patterns regexes that match the answer
  unsourced_practice  sentences that claim court practice ("სასამართლო პრაქტიკა", "დამკვიდრებული განმარტებით",
                      "უზენაესი სასამართლოს განმარტებით" ...) with no case number in the same sentence
  refusal             refusal markers present (for unlawful requests)
  lawyer_referral     a lawyer is mentioned
  latin_words         Latin-script words outside links and quotes (language proxy)
  only_codes          the set of codes cited (for the work-mention trap: an all-Labour-Code answer fails)
"""
from __future__ import annotations

import re
import sqlite3
from functools import lru_cache
from pathlib import Path

SUP = str.maketrans("¹²³⁴⁵⁶⁷⁸⁹⁰", "1234567890")
CODES = [
    ("civil_procedure_code", r"სამოქალაქო\s+საპროცესო\s+კოდექს"),
    ("criminal_procedure_code", r"სისხლის\s+სამართლის\s+საპროცესო\s+კოდექს"),
    ("admin_offences_code", r"ადმინისტრაციულ\s+სამართალდარღვევათა\s+კოდექს"),
    ("admin_procedure_code", r"ადმინისტრაციული\s+საპროცესო\s+კოდექს"),
    ("general_admin_code", r"ზოგადი\s+ადმინისტრაციული\s+კოდექს"),
    ("criminal_code", r"სისხლის\s+სამართლის\s+კოდექს"),
    ("civil_code", r"სამოქალაქო\s+კოდექს"),
    ("labour_code", r"შრომის\s+კოდექს"),
    ("constitution", r"კონსტიტუცი"),
    ("tax_code", r"საგადასახადო\s+კოდექს"),
    ("election_code", r"საარჩევნო\s+კოდექს"),
    ("personal_data_law", r"პერსონალურ\s+მონაცემთა\s+დაცვის\s+შესახებ"),
]
CODE_RE = re.compile("|".join(f"(?P<{k}>{p})" for k, p in CODES))
OTHER_LAW_RE = re.compile(r"„[^“”\"]{3,120}?(?:შესახებ|კანონი)[“”\"]\s*(?:საქართველოს\s+)?(?:ორგანული\s+)?კანონ|(?<!კოდექსის )\bკანონის\s+(?=\d)")
NUM = r"(\d+(?:[¹²³⁴⁵⁶⁷⁸⁹⁰]+)?)"
ART_PATTERNS = [
    re.compile(r"მუხლ(?:ი|ის|ით|ში|ზე)\s+" + NUM),
    re.compile(r"(?:მე-)?" + NUM + r"(?:-ე|-ის|-ე)?\s*მუხლ"),
    re.compile(r"მუხ\.\s*" + NUM),
]
LINK_RE = re.compile(r"matsne\.gov\.ge/ka/document/view/(\d+)(?:\?[^#)\s]*)?#article_(\d+)")
PARA_RE = re.compile(r"^[^.\n]{0,25}?(?:(?:მე-)?(\d+)(?:-ე)?\s+(?:პუნქტ|ნაწილ)|(?:პუნქტ|ნაწილ)(?:ი|ის)\s+(\d+)|(პირველი)\s+(?:პუნქტ|ნაწილ))")

# Named deadline / amount patterns used by expected.required_numbers.
NUMBER_PATTERNS = {
    "14d": r"(?:\b14|თოთხმეტ)\s*(?:-?\s*(?:კალენდარულ|სამუშაო)\S*\s*)?დღ",
    "21d": r"(?:\b21|ოცდაერთ)\s*(?:-?\s*(?:კალენდარულ|სამუშაო)\S*\s*)?დღ",
    "30d": r"(?:\b30|ოცდაათ)\s*(?:-?\s*(?:კალენდარულ|სამუშაო)\S*\s*)?დღ",
    "10d": r"(?:\b10|ათ)\s*(?:-?\s*(?:კალენდარულ|სამუშაო)\S*\s*)?დღ",
    "7d": r"(?:\b7|შვიდ)\s*(?:-?\s*(?:კალენდარულ|სამუშაო)\S*\s*)?დღ",
    "1m": r"(?:\b1|ერთ)\s*(?:-?\s*)?თვ",
    "6m": r"(?:\b6|ექვს)\s*(?:-?\s*)?თვ",
    "3y": r"(?:\b3|სამ)\s*(?:-?\s*)?წ(?:ელ|ლ)|სამწლიან",
    "2y": r"(?:\b2|ორ)\s*(?:-?\s*)?წ(?:ელ|ლ)",
    "18y": r"(?:\b18|თვრამეტ)\s*(?:-?\s*)?წ(?:ელ|ლ)",
    "48h": r"(?:\b48|ორმოცდარვა)\s*(?:-?\s*)?საათ",
    "72h": r"(?:\b72|სამოცდათორმეტ)\s*(?:-?\s*)?საათ",
    "40h": r"(?:\b40|ორმოც)\s*(?:-?\s*)?საათ",
    "0.07pct": r"0[.,]07\s*%",
}

PRACTICE_RE = re.compile(
    r"სასამართლო(?:ს)?\s+პრაქტიკ|დამკვიდრებულ\w*\s+(?:პრაქტიკ|განმარტებ|მიდგომ)|"
    r"უზენაესი\s+სასამართლოს\s+(?:\w+\s+)?(?:განმარტებ|პრაქტიკ|მიდგომ|პოზიცი)|"
    r"საკასაციო\s+პალატის\s+(?:\w+\s+)?(?:განმარტებ|პრაქტიკ|მიდგომ)|პრაქტიკის\s+მიხედვით|პრაქტიკაში\s+(?:სასამართლოები|მიიჩნევა)")
# Quoting the statutory admissibility grounds ("uniform court practice", "departs from practice") is not a claim.
ADMISSIBILITY_RE = re.compile(r"ერთგვაროვან|ჩამოყალიბ|გადახვევ|გადაუხვი|განსხვავდება\s+[^.]{0,40}პრაქტიკ")
CASE_NO_RE = re.compile(r"(?:№|N|#)\s*[ასბ]{0,2}[ასბ]-?\s*\d+|\b(?:ას|ბს|სს)-\d+|\d+\s*აპ-\d+|\b\d+ap-\d+|საქმე\s*(?:№|N)\s*\S+|\d+/\d+/\d+")
REFUSAL_RE = re.compile(r"ვერ\s+დაგეხმარებ|ვერ\s+გაგიწევ|არ\s+შემიძლია\s+(?:დაგეხმარ|მოგცე|გაგიწი|გასწავლ)|ვერ\s+მოგცემ|უარს\s+ვაცხადებ|"
                        r"ვერ\s+გასწავლი|არ\s+დაგეხმარებ|ვერ\s+შევასრულებ|არ\s+მივცემ")
LAWYER_RE = re.compile(r"ადვოკატ|იურისტ|სამართლებრივი\s+დახმარების\s+სამსახურ")
LATIN_WORD_RE = re.compile(r"\b[A-Za-z]{3,}\b")
URL_RE = re.compile(r"https?://\S+|\[[^\]]*\]\([^)]*\)")


@lru_cache(maxsize=2)
def load_store(store_path: str):
    conn = sqlite3.connect(f"file:{store_path}?mode=ro", uri=True)
    arts, docnum = {}, {}
    for doc_id, norm, title, text, url, rep in conn.execute(
            "SELECT document_id, article_norm, article_title, content_ka, article_url, is_repealed FROM articles"):
        arts.setdefault((doc_id, norm), []).append({"title": title or "", "text": text, "repealed": bool(rep)})
        m = re.search(r"document/view/(\d+)", url or "")
        if m:
            docnum[m.group(1)] = doc_id
    conn.close()
    return arts, docnum


def _code_before(text: str, pos: int, window: int = 160):
    seg = text[max(0, pos - window):pos]
    last = None
    for m in CODE_RE.finditer(seg):
        last = m
    other = None
    for m in OTHER_LAW_RE.finditer(seg):
        other = m
    if other and (not last or other.start() > last.start()):
        return "other_law"
    return last.lastgroup if last else None


def sentence_at(text: str, pos: int) -> str:
    s = max(text.rfind("\n", 0, pos), text.rfind(". ", 0, pos))
    ends = [i for i in (text.find("\n", pos), text.find(". ", pos)) if i != -1]
    return text[s + 1:(min(ends) if ends else len(text)) + 1].strip()[:600]


def extract_citations(text: str, store_path: str) -> list[dict]:
    """Cited articles with existence status, deduplicated by (code, article, paragraph)."""
    arts, docnum = load_store(store_path)
    found, spans = [], []
    for m in LINK_RE.finditer(text):
        found.append({"code": docnum.get(m.group(1), f"doc:{m.group(1)}"), "article": m.group(2), "paragraph": None,
                      "pos": m.start(), "via": "link", "superscript": False})
        spans.append((m.start(), m.end()))
    for pat in ART_PATTERNS:
        for m in pat.finditer(text):
            if any(a <= m.start() < b for a, b in spans):
                continue
            raw = m.group(1)
            pm = PARA_RE.search(text[m.end():m.end() + 60])
            para = ("1" if pm.group(3) else (pm.group(1) or pm.group(2))) if pm else None
            found.append({"code": _code_before(text, m.start()) or "unknown_code", "article": raw.translate(SUP),
                          "paragraph": para, "pos": m.start(), "via": "text", "superscript": raw != raw.translate(SUP)})
    uniq = {}
    for c in sorted(found, key=lambda c: c["pos"]):
        uniq.setdefault((c["code"], c["article"], c["paragraph"]), c)
    uniq = {k: v for k, v in uniq.items() if k[2] or not any(o[:2] == k[:2] and o[2] for o in uniq)}
    out = []
    for (code, art, para), c in uniq.items():
        e = {"code": code, "article": art, "paragraph": para, "via": c["via"], "superscript": c["superscript"],
             "context": sentence_at(text, c["pos"])}
        if code == "other_law":
            e["status"] = "other_law"
        elif code == "unknown_code" or code.startswith("doc:"):
            e["status"] = "unknown_code"
        else:
            rows = arts.get((code, art))
            if not rows:
                e["status"] = "nonexistent"
            else:
                live = [r for r in rows if not r["repealed"] and "ამოღებულია" not in r["title"][:30]]
                row = (live or rows)[0]
                e["article_title"], e["article_text"] = row["title"], row["text"][:2500]
                if not live:
                    e["status"] = "repealed"
                elif para and not re.search(rf"(?m)^\s*{re.escape(para)}\.\s", row["text"]):
                    e["status"] = "paragraph_missing"
                else:
                    e["status"] = "exists"
        out.append(e)
    return out


def unsourced_practice(text: str) -> list[str]:
    hits = []
    for m in PRACTICE_RE.finditer(text):
        sent = sentence_at(text, m.start())
        if not CASE_NO_RE.search(sent) and not ADMISSIBILITY_RE.search(sent):
            hits.append(sent[:300])
    return list(dict.fromkeys(hits))


def run_checks(rec: dict, expected: dict, store_path: str) -> dict:
    body = rec.get("body") or {}
    text = (body.get("response") or "").strip()
    res: dict = {"status": rec.get("status"), "latency_s": rec.get("latency_s"), "degraded": bool(rec.get("degraded")),
                 "answer_chars": len(text)}
    res["empty_or_broken"] = rec.get("status") != 200 or len(text) < 40
    cites = extract_citations(text, store_path) if text else []
    res["citations"] = cites
    res["citation_counts"] = {}
    for c in cites:
        res["citation_counts"][c["status"]] = res["citation_counts"].get(c["status"], 0) + 1
    res["invented_articles"] = [f"{c['code']}:{c['article']}" for c in cites if c["status"] == "nonexistent"]
    cited = {(c["code"], c["article"]) for c in cites}
    missing_groups = []
    for group in expected.get("required_articles", []):
        if not any(tuple(ref.split(":")) in cited for ref in group):
            missing_groups.append(group)
    res["required_articles_missing"] = missing_groups
    res["required_numbers_missing"] = [k for k in expected.get("required_numbers", [])
                                       if not re.search(NUMBER_PATTERNS[k], text)]
    res["forbidden_patterns_hit"] = [p for p in expected.get("must_not_patterns", []) if re.search(p, text)]
    res["unsourced_practice"] = unsourced_practice(text)
    res["refusal_marker"] = bool(REFUSAL_RE.search(text)) or ((rec.get("guardrail") or {}).get("should_proceed") is False)
    res["lawyer_referral"] = bool(LAWYER_RE.search(text))
    plain = URL_RE.sub(" ", text)
    plain = re.sub(r"\([^)]*[A-Za-z][^)]*\)", " ", plain)
    res["latin_words"] = len(LATIN_WORD_RE.findall(plain))
    codes = {c["code"] for c in cites if c["status"] in ("exists", "paragraph_missing", "repealed")}
    res["codes_cited"] = sorted(codes)
    forbid_only = set(expected.get("forbid_only_codes", []))
    res["only_forbidden_codes"] = bool(forbid_only) and bool(codes) and codes <= forbid_only
    return res
