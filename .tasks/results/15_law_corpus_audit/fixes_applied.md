# Fixes Applied — Code Changes

> Exact changes made to fix bugs 1-5. Each section shows the file, diff, and rationale.

---

## Fix 1: HTML Parser — Article Number Fallback

**File:** `law_corpus/pipeline/parser/html_parser.py`
**Commit scope:** Lines 182-208

### Before (buggy)
```python
else:
    current_article_num = text
    current_article_title = None
```

### After (fixed)
```python
else:
    # Fallback: try to extract article number from malformed text.
    # Common case: "მუხლი7.სრულისათაური" (no space after მუხლი)
    fallback_m = re.search(r"მუხლი\s*(\d+)", text)
    if fallback_m:
        current_article_num = normalise_superscripts(fallback_m.group(1))
        # Extract title: everything after "number." or "number "
        title_m = re.search(r"\d+\s*[.\-–—]\s*(.*)", text)
        current_article_title = title_m.group(1).strip() if title_m else None
    else:
        # Last resort: log warning and use sanitised text
        logger.warning("Unparseable article header: %s", text[:80])
        current_article_num = text
        current_article_title = None
```

### Rationale
- `\s*` instead of `\s+` catches the zero-space case (`მუხლი7`)
- Still falls back to raw text if no number found (with a warning log)
- Also extracts the title when possible

### Regression Tests
3 tests in `law_corpus/tests/test_parser.py::TestArticleNumberFallback`:
- `test_no_space_article_header` — `მუხლი7.Title` → `მუხლი 7`
- `test_no_space_with_superscript_suffix` — `მუხლი276.Title` → `მუხლი 276`
- `test_standard_article_still_works` — `მუხლი 45. Title` → `მუხლი 45` (no regression)

---

## Fix 2: Threshold Ingestion — Code Name Canonicalization

**File:** `law_corpus/ingest_thresholds.py`
**Commit scope:** Added `_canonicalize_code_name()` function + mapping dict

### Added Code
```python
_CODE_NAME_CANONICAL: dict[str, str] = {
    "სისხლის სამართლის კოდექსი": "საქართველოს სისხლის სამართლის კოდექსი",
    "სამოქალაქო კოდექსი": "საქართველოს სამოქალაქო კოდექსი",
    "სისხლის სამართლის საპროცესო კოდექსი": "საქართველოს სისხლის სამართლის საპროცესო კოდექსი",
    "ადმინისტრაციულ სამართალდარღვევათა კოდექსი": "საქართველოს ადმინისტრაციულ სამართალდარღვევათა კოდექსი",
    "შრომის კოდექსი": "საქართველოს შრომის კოდექსი",
    "საგადასახადო კოდექსი": "საქართველოს საგადასახადო კოდექსი",
    "სამოქალაქო საპროცესო კოდექსი": "საქართველოს სამოქალაქო საპროცესო კოდექსი",
    "საარჩევნო კოდექსი": "საქართველოს საარჩევნო კოდექსი",
    "ზოგადი ადმინისტრაციული კოდექსი": "საქართველოს ზოგადი ადმინისტრაციული კოდექსი",
    "ადმინისტრაციული საპროცესო კოდექსი": "საქართველოს ადმინისტრაციული საპროცესო კოდექსი",
}

def _canonicalize_code_name(raw: str) -> str:
    return _CODE_NAME_CANONICAL.get(raw, raw)
```

### Applied In
- `build_threshold_metadata()` — `"code_name": _canonicalize_code_name(entry["code_name"])`
- `build_threshold_document()` — `f"კოდექსი: {_canonicalize_code_name(entry['code_name'])}"`

### Rationale
- Mapping is explicit and auditable (no heuristics)
- Unknown names pass through unchanged (narcotics law, personal data law)
- Applied to both metadata AND the document text (so embedding matches)

### Regression Tests
6 tests in `law_corpus/tests/test_parser.py::TestThresholdCodeNameCanonical`:
- Criminal, civil, labor code canonicalization
- Already-canonical names unchanged
- Narcotics law pass-through
- `build_threshold_metadata` integration test

---

## Fix 3+4+5: Citation Service — Ordering, Missing Codes, Abbreviations

**File:** `backend/app/services/citation_service.py`
**Commit scope:** Rewrote `CODE_NAMES` list + added `_ABBREVIATION_MAP` + `_ABBREV_PATTERN`

### Changes Made

**1. CODE_NAMES reordered longest-first:**
```python
CODE_NAMES = [
    # Full canonical forms (longest — checked first)
    "საქართველოს ადმინისტრაციულ სამართალდარღვევათა კოდექსი",
    "საქართველოს სისხლის სამართლის საპროცესო კოდექსი",
    ...
    # Short forms (shorter — checked after full forms)
    "ადმინისტრაციულ სამართალდარღვევათა კოდექსი",
    "სისხლის სამართლის საპროცესო კოდექსი",
    ...
]
```

**2. Added missing `საარჩევნო კოდექსი`** (both full and short form)

**3. Added abbreviation map and regex:**
```python
_ABBREVIATION_MAP = {
    "სსკ": "საქართველოს სისხლის სამართლის კოდექსი",
    "სკ": "საქართველოს სამოქალაქო კოდექსი",
    "სსსკ": "საქართველოს სისხლის სამართლის საპროცესო კოდექსი",
    "სსპკ": "საქართველოს სისხლის სამართლის საპროცესო კოდექსი",
    "სპკ": "საქართველოს სამოქალაქო საპროცესო კოდექსი",
    "ზაკ": "საქართველოს ზოგადი ადმინისტრაციული კოდექსი",
    "ასდკ": "საქართველოს ადმინისტრაციულ სამართალდარღვევათა კოდექსი",
}
```

**4. Updated `_find_code_name()` to check abbreviations first:**
```python
# Check abbreviations first (e.g. "სსკ-ის 177-ე მუხლი")
for abbrev_m in _ABBREV_PATTERN.finditer(preceding):
    if abbrev_m.end() > best_pos:
        best_pos = abbrev_m.end()
        best_name = _ABBREVIATION_MAP[abbrev_m.group(1)]
```

### Rationale
- Longest-first ordering prevents short-form from shadowing long-form
- Abbreviation map is explicit — each abbreviation resolves to the full canonical name
- `_ABBREV_PATTERN` handles suffixes like `სსკ-ის`, `სსკ-ით`

---

## Files Changed Summary

```
law_corpus/pipeline/parser/html_parser.py    | +16 lines (fallback regex)
law_corpus/ingest_thresholds.py              | +25 lines (canonicalization)
law_corpus/tests/test_parser.py              | +145 lines (9 regression tests)
backend/app/services/citation_service.py     | +54 -30 lines (ordering + abbreviations)
```

All changes are in version control (uncommitted). Run `git diff` to see exact diffs.
