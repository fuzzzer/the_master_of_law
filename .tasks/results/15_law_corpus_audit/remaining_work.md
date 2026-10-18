# Remaining Work — Open Bugs & Next Steps

> 2 bugs remain unfixed. This document describes what needs to be done.

---

## Bug 6: `extract_norm_interpretation` — Grand Chamber Metadata

**File:** `law_corpus/pipeline/court/chunker.py` lines 91-112
**Impact:** 0/177 grand_chamber chunks have useful `norm_interpreted` metadata
**Effort:** ~1 hour

### Current Code (broken)

```python
def extract_norm_interpretation(text: str) -> dict[str, str]:
    result = {}
    norm_match = re.search(
        r'(სსკ|სამოქალაქო\s+კოდექსის?|სპკ|ადმინისტრაციული)\s+(\d+)',
        text[:1000],  # ← too narrow
    )
    if norm_match:
        result["norm_interpreted"] = norm_match.group(0)
    # ...
```

### What Needs to Change

1. **Expand search window** from 1000 to 3000 chars
2. **Add more code name patterns**: `სისხლის\s+სამართლის`, `შრომის\s+კოდექს`, `საგადასახადო` etc.
3. **Fix binding_rule regex** — currently matches table of contents. Should require at least 10 chars of meaningful content after the trigger word.
4. **Add unit tests** — test with real grand chamber case file excerpts

### Proposed Fix

```python
def extract_norm_interpretation(text: str) -> dict[str, str]:
    result = {}
    search_window = text[:3000]

    norm_match = re.search(
        r'(სსკ|სკ|სსსკ|სპკ|ზაკ|ასდკ|'
        r'სისხლის\s+სამართლის\s+კოდექს\w*|'
        r'სამოქალაქო\s+კოდექს\w*|'
        r'ადმინისტრაციული\s+საპროცესო|'
        r'ზოგადი\s+ადმინისტრაციული|'
        r'შრომის\s+კოდექს\w*|'
        r'საგადასახადო\s+კოდექს\w*)'
        r'[^.]*?(\d+)',
        search_window,
    )
    if norm_match:
        result["norm_interpreted"] = norm_match.group(0).strip()

    rule_match = re.search(
        r'(დადგენილია\s+[^.]{10,200}|'
        r'სავალდებულო\s+ინტერპრეტაცია[^.]{10,200})\.',
        text[:5000],
    )
    if rule_match:
        result["binding_rule"] = rule_match.group(0)[:200]

    return result
```

### After Fixing

Re-run the court embedding pipeline for `grand_chamber`:
```bash
cd law_corpus
python -m pipeline.court.embed_pipeline --collection grand_chamber --rebuild
```

---

## Bug 7: `law_browser_service.get_code()` — Wrong Filter Key

**File:** `backend/app/services/law_browser_service.py` lines 76-77
**Impact:** `/api/v1/laws/{code_id}` endpoint returns empty data
**Effort:** ~30 minutes

### Current Code (broken)

```python
results = self.chroma.collection.get(
    where={"code_name": code_id},  # code_id = "criminal_code" (English!)
)
```

### What Needs to Change

Add a mapping from English code slugs to Georgian canonical names:

```python
_CODE_ID_TO_NAME: dict[str, str] = {
    "criminal_code": "საქართველოს სისხლის სამართლის კოდექსი",
    "civil_code": "საქართველოს სამოქალაქო კოდექსი",
    "admin_offences_code": "საქართველოს ადმინისტრაციულ სამართალდარღვევათა კოდექსი",
    "criminal_procedure_code": "საქართველოს სისხლის სამართლის საპროცესო კოდექსი",
    "civil_procedure_code": "საქართველოს სამოქალაქო საპროცესო კოდექსი",
    "labor_code": "საქართველოს შრომის კოდექსი",
    "tax_code": "საქართველოს საგადასახადო კოდექსი",
    "election_code": "საქართველოს საარჩევნო კოდექსი",
    "general_admin_code": "საქართველოს ზოგადი ადმინისტრაციული კოდექსი",
    "admin_procedure_code": "საქართველოს ადმინისტრაციული საპროცესო კოდექსი",
    "constitution": "საქართველოს კონსტიტუცია",
    "narcotics_law": "ნარკოტიკული საშუალებების შესახებ კანონი",
    "personal_data_law": "პერსონალურ მონაცემთა დაცვის შესახებ",
}
```

Then update `get_code()`:
```python
def get_code(self, code_id: str) -> dict[str, Any] | None:
    # ...
    if isinstance(data, list):
        # Map English slug to Georgian name for ChromaDB filter
        georgian_name = _CODE_ID_TO_NAME.get(code_id, code_id)
        results = self.chroma.collection.get(
            where={"code_name": georgian_name},
            include=["documents", "metadatas"]
        )
```

### Verification

```bash
# After fix, test the endpoint:
curl http://localhost:8000/api/v1/laws/criminal_code | python3 -m json.tool | head -20
# Should return actual chunks, not empty
```

---

## Other Improvements (Not Bugs, Nice-to-Have)

### `detect_year()` in court/chunker.py
- Current regex: `20(2[0-6]|1\d|0\d)` — will break in 2027
- Fix: Change to `20(2\d|1\d|0\d)` or `20\d{2}`
- Low priority — harmless until January 2027

### Threshold `consequence_ka` field
- Some entries have malformed consequence text with `>` and `≤` symbols that may not render correctly
- Low priority — cosmetic only

### Grand chamber category detection
- `detect_category()` uses English path substrings (`"criminal"`, `"civil"`)
- Works because the extracted files are already organized in English-named folders
- Would break if someone reorganizes the folder structure — but low risk
