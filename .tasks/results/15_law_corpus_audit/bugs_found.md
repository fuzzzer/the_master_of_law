# Bugs Found — Full Root Cause Analysis

> 7 bugs found across 5 files during the law corpus pipeline audit.

---

## Bug 1: Malformed `article_number` in HTML Parser (60 chunks)

**Severity:** 🔴 Critical — AI citations broken for affected articles
**File:** `law_corpus/pipeline/parser/html_parser.py` lines 182-196
**Affected data:** ~60 chunks in `georgian_laws` collection

### What Happened

When an HTML page from matsne.gov.ge has a `<p class="muxlixml">` tag where the text has **no space** between `მუხლი` and the number (e.g. `მუხლი7.საარჩევნო ადმინისტრაციის სტატუსი`), the primary regex `ARTICLE_RE` fails to match.

The fallback code used the **entire raw text** as `article_num`:
```python
else:
    current_article_num = text  # ← BUG: "მუხლი7.საარჩევნო ადმინისტრაციის სტატუსი"
    current_article_title = None
```

Then `_flush_article()` line 285 prepends `მუხლი `:
```python
article_number = f"მუხლი {article_num}"
# Result: "მუხლი მუხლი7.საარჩევნო ადმინისტრაციის სტატუსი"
```

### Root Cause
The `ARTICLE_RE` regex requires `\s+` (one or more whitespace) between `მუხლი` and the number. Some matsne.gov.ge pages don't have this space.

### How to Reproduce
```python
import re
ARTICLE_RE = re.compile(r"მუხლი\s+(\d+(?:[⁰¹²³⁴⁵⁶⁷⁸⁹]+|\-\d+)?)\s*[.\-–—]?\s*(.*)", re.UNICODE)
assert ARTICLE_RE.search("მუხლი7.სათაური") is None  # ← fails, no space
assert ARTICLE_RE.search("მუხლი 7. სათაური") is not None  # ← works, has space
```

---

## Bug 2: Short-Form `code_name` in Threshold Chunks (20 chunks)

**Severity:** 🔴 Critical — threshold data can't be linked to its parent code
**File:** `law_corpus/ingest_thresholds.py` lines 43-53
**Affected data:** 20 threshold chunks in `georgian_laws` collection

### What Happened

`threshold_catalog.json` stores code names **without** the `საქართველოს` prefix:
```json
{"code_name": "სისხლის სამართლის კოდექსი"}
```

But the main georgian_laws pipeline stores them **with** the prefix:
```
"საქართველოს სისხლის სამართლის კოდექსი"
```

`build_threshold_metadata()` passed the catalog value straight through:
```python
"code_name": entry["code_name"],  # ← short form, inconsistent
```

### Root Cause
No normalization layer between the JSON catalog and ChromaDB ingestion.

---

## Bug 3: Short Form Shadows Long Form in Citation Service

**Severity:** 🔴 Critical — citations matched to wrong code name
**File:** `backend/app/services/citation_service.py` lines 25-112
**Affected behavior:** Every citation extraction call

### What Happened

`CODE_NAMES` list had both long and short forms in arbitrary order:
```python
CODE_NAMES = [
    "საქართველოს სამოქალაქო კოდექსი",  # long form at pos 1
    ...
    "სამოქალაქო კოდექსი",  # short form at pos 13
]
```

`_find_code_name()` uses `rfind()` to search backwards. When the text contains the full form `"საქართველოს სამოქალაქო კოდექსი"`:
- `rfind("საქართველოს სამოქალაქო კოდექსი")` matches at position 0
- `rfind("სამოქალაქო კოდექსი")` matches at position 13 (INSIDE the long form!)

Since 13 > 0, the **short form wins** as "closest match". The citation would be recorded as `"სამოქალაქო კოდექსი"` instead of `"საქართველოს სამოქალაქო კოდექსი"`.

### Root Cause
No ordering guarantee on CODE_NAMES + `rfind` prefers later positions without considering match specificity.

---

## Bug 4: Missing `საარჩევნო კოდექსი` from CODE_NAMES

**Severity:** 🟡 Medium — 1,729 election code chunks invisible to citation checker
**File:** `backend/app/services/citation_service.py` line 25

### What Happened

`საქართველოს საარჩევნო კოდექსი` (Election Code) was entirely missing from the `CODE_NAMES` list. When the AI generates text referencing election law articles, the citation service can never find the code name → marks it as `"Unknown"`.

---

## Bug 5: No Abbreviation Support in Citation Extraction

**Severity:** 🟡 Medium — common AI output format unrecognized
**File:** `backend/app/services/citation_service.py`

### What Happened

The Gemini model frequently uses standard Georgian legal abbreviations:
- `სსკ` → სისხლის სამართლის კოდექსი (Criminal Code)
- `სკ` → სამოქალაქო კოდექსი (Civil Code)
- `სსსკ` → სისხლის სამართლის საპროცესო კოდექსი (Criminal Procedure Code)

Example AI output: `"სსკ-ის 177-ე მუხლით გათვალისწინებული..."`

The citation service had no way to resolve these abbreviations → marked all as `code_name: "Unknown"`.

---

## Bug 6: `extract_norm_interpretation` Nearly Useless (15% hit rate)

**Severity:** 🟡 Medium — grand chamber metadata quality issue
**File:** `law_corpus/pipeline/court/chunker.py` lines 91-112
**Status:** ❌ NOT YET FIXED

### What Happens

The function searches only the first 1000 characters for a narrow set of patterns:
```python
norm_match = re.search(
    r'(სსკ|სამოქალაქო\s+კოდექსის?|სპკ|ადმინისტრაციული)\s+(\d+)',
    text[:1000],  # ← too narrow window
)
```

**Problems:**
1. **Window too small:** Most case files mention the interpreted norm AFTER the 1000-char header
2. **Garbage matches:** The `binding_rule` regex matches `განმარტებანი` + table of contents text
3. **Missing patterns:** Doesn't match `სისხლის სამართლის კოდექსი`, `შრომის კოდექსი`, etc.

**Result:** Only 6 of 40 files (15%) get `norm_interpreted`, and those 6 have garbage data.

---

## Bug 7: `law_browser_service.get_code()` Uses Wrong Filter Key

**Severity:** 🟡 Medium — law browser endpoint returns empty data
**File:** `backend/app/services/law_browser_service.py` lines 76-77
**Status:** ❌ NOT YET FIXED

### What Happens

```python
results = self.chroma.collection.get(
    where={"code_name": code_id},  # code_id = "criminal_code" (English slug!)
)
```

ChromaDB stores `code_name` as: `"საქართველოს სისხლის სამართლის კოდექსი"` (Georgian)

The filter `{"code_name": "criminal_code"}` will **never match** → always returns 0 results.

The `/api/v1/laws/{code_id}` endpoint silently returns empty data for any code.
