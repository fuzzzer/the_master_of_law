# Law Corpus Audit — Technical Specs & Acceptance Criteria

## 1. ChromaDB Data Location

```
law_corpus/data/chroma/          # ChromaDB persistent storage (~876MB)
law_corpus/data/thresholds/      # threshold_catalog.json (380 entries)
law_corpus/data/georgian_laws/   # JSON indices (article_index.json, code_index.json)
law_corpus/data/court_practice/  # Source text files
law_corpus/data/grand_chamber/   # Source text files
```

## 2. Collection Schemas

### `georgian_laws` (15,718 chunks)

Required metadata fields (all must be non-empty):

| Field | Example | Required |
|-------|---------|----------|
| `code_name` | `საქართველოს სისხლის სამართლის კოდექსი` | ✅ Must use **full form** with `საქართველოს` prefix |
| `article_number` | `მუხლი 177` | ✅ |
| `article_title` | `ქურდობა` | ✅ |
| `article_url` | `https://matsne.gov.ge/ka/document/view/16426#article_177` | ✅ |
| `citation_text` | `საქართველოს სისხლის სამართლის კოდექსი, მუხლი 177, (#2287)` | ✅ |
| `source_url` | `https://matsne.gov.ge/ka/document/view/16426` | ✅ |
| `document_id` | `criminal_code` | ✅ |
| `chunk_index` | `0` | ✅ |

**Known issue**: 20 chunks have short-form `code_name`:
```
15 × "სისხლის სამართლის კოდექსი"          → "საქართველოს სისხლის სამართლის კოდექსი"
 2 × "სისხლის სამართლის საპროცესო კოდექსი" → "საქართველოს სისხლის სამართლის საპროცესო კოდექსი"
 1 × "სამოქალაქო კოდექსი"                  → "საქართველოს სამოქალაქო კოდექსი"
 1 × "ადმინისტრაციულ სამართალდარღვევათა კოდექსი" → "საქართველოს ადმინისტრაციულ სამართალდარღვევათა კოდექსი"
 1 × "შრომის კოდექსი"                      → "საქართველოს შრომის კოდექსი"
```

### `court_practice` (4,618 chunks)

| Field | Example | Status |
|-------|---------|--------|
| `case_id` | `07აპ` | ✅ Present |
| `category` | `criminal` / `civil` / `administrative` | ✅ Present |
| `year` | `2022` | ✅ Present |
| `court` | `supreme_court` | ✅ Present |
| `section` | `general` / `reasoning` / `resolution` | ✅ Present |
| `source_file` | `07აპ.txt` | ✅ Present |
| `articles_cited` | `["მუხლი 177", "მუხლი 19"]` | ❌ **Missing** — should be extracted |

### `grand_chamber` (177 chunks)

| Field | Example | Status |
|-------|---------|--------|
| `case_id` | `53-კ` | ✅ Present |
| `category` | `criminal` / `civil` / `administrative` | ✅ Present |
| `year` | `2005` | ✅ Present |
| `binding_rule` | Text of the binding principle | ⚠️ **43/177 populated** (24%) |
| `norm_interpreted` | `მუხლი 120` | ❌ **0/177 populated** (0%) |

### Threshold Catalog (380 entries)

| Field | Required | Issue |
|-------|----------|-------|
| `substance` | Required for `drug_quantity` type | ⚠️ Some entries have `None` |

## 3. Code Name Mapping (Canonical Forms)

Two names are OK without `საქართველოს` prefix (they don't have one in official documents):
- `ნარკოტიკული საშუალებების შესახებ კანონი`
- `პერსონალურ მონაცემთა დაცვის შესახებ`

All others MUST have `საქართველოს` prefix. The full canonical list:

```python
CANONICAL_CODE_NAMES = [
    "საქართველოს სისხლის სამართლის კოდექსი",
    "საქართველოს სამოქალაქო კოდექსი",
    "საქართველოს ადმინისტრაციულ სამართალდარღვევათა კოდექსი",
    "საქართველოს სისხლის სამართლის საპროცესო კოდექსი",
    "საქართველოს სამოქალაქო საპროცესო კოდექსი",
    "საქართველოს შრომის კოდექსი",
    "საქართველოს საგადასახადო კოდექსი",
    "საქართველოს კონსტიტუცია",
    "საქართველოს ზოგადი ადმინისტრაციული კოდექსი",
    "საქართველოს ადმინისტრაციული საპროცესო კოდექსი",
    "საქართველოს საარჩევნო კოდექსი",
    "ნარკოტიკული საშუალებების შესახებ კანონი",  # No prefix
    "პერსონალურ მონაცემთა დაცვის შესახებ",       # No prefix
]
```

## 4. ChromaDB Update API

```python
import chromadb

client = chromadb.PersistentClient(path="law_corpus/data/chroma")
col = client.get_collection("georgian_laws")

# Update metadata for specific chunks
col.update(
    ids=["chunk_id_1", "chunk_id_2"],
    metadatas=[
        {"code_name": "საქართველოს სისხლის სამართლის კოდექსი", ...existing_meta},
        {"code_name": "საქართველოს სისხლის სამართლის კოდექსი", ...existing_meta},
    ],
)
```

**CRITICAL**: When updating metadata, you must pass ALL existing metadata fields, not just the changed one. ChromaDB's `update()` replaces the entire metadata dict.

## 5. Go/No-Go Criteria

- [ ] Audit script produces clean report
- [ ] 0 chunks with short-form `code_name` in `georgian_laws`
- [ ] `norm_interpreted` populated in ≥ 80% of `grand_chamber` chunks
- [ ] `binding_rule` populated in ≥ 80% of `grand_chamber` chunks
- [ ] 0 `None` substance fields in threshold catalog for `drug_quantity` type
- [ ] `search_by_metadata(article_number="მუხლი 177", code_name="საქართველოს სისხლის სამართლის კოდექსი")` returns ≥1 result
- [ ] Backend test suite passes: `cd backend && python -m pytest tests/ --ignore=tests/scripts -q` → 0 failures
- [ ] Ingestion pipeline updated to prevent regression
