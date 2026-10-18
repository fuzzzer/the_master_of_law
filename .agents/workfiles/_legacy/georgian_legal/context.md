# ⚖️ Georgian Legal — Skill Context

> **When to load:** Working with Georgian law content, translations, citation formats, legal terminology.

---

## Georgian Legal System Structure

### Court Hierarchy
```
საკონსტიტუციო სასამართლო (Constitutional Court)
საქართველოს უზენაესი სასამართლო (Supreme Court)
  └── სააპელაციო სასამართლოები (Courts of Appeal) — 2 total
       └── რაიონული/საქალაქო სასამართლოები (District Courts)
```

### Legal Codes in Corpus (12 total)

| Code (Georgian) | Code (English) | Articles | Priority |
|-----------------|---------------|----------|----------|
| საქართველოს კონსტიტუცია | Constitution | ~120 | P0 |
| სისხლის სამართლის კოდექსი | Criminal Code | ~400 | P0 |
| სამოქალაქო კოდექსი | Civil Code | ~1500 | P0 |
| ადმინისტრაციულ სამართალდარღვევათა კოდექსი | Administrative Code | ~300 | P0 |
| შრომის კოდექსი | Labor Code | ~60 | P0 |
| საგადასახადო კოდექსი | Tax Code | ~300 | P1 |
| ადმინისტრაციული საპროცესო კოდექსი | Admin Procedure Code | ~250 | P1 |
| სამოქალაქო საპროცესო კოდექსი | Civil Procedure Code | ~400 | P1 |
| სისხლის სამართლის საპროცესო კოდექსი | Criminal Procedure | ~350 | P1 |
| საოჯახო სამართალი | Family Law | ~100 | P1 |
| საკუთრების სამართალი | Property Law | ~80 | P1 |
| მონაცემთა დაცვა | Data Protection | ~40 | P1 |

---

## Citation Format

### Standard Pattern
```
საქართველოს [კოდექსის სახელი], მუხლი [ნომერი]
```

**Examples:**
- `საქართველოს სისხლის სამართლის კოდექსი, მუხლი 177` (Criminal Code, Article 177)
- `საქართველოს სამოქალაქო კოდექსი, მუხლი 316` (Civil Code, Article 316)

### Regex for Citation Extraction
```python
import re
# Matches "მუხლი" followed by digits (with optional sub-articles)
CITATION_PATTERN = re.compile(
    r'მუხლი\s+(\d+(?:\.\d+)?(?:\s*[-–]\s*\d+)?)',
    re.UNICODE
)
```

### URL Format (matsne.gov.ge)
```
https://matsne.gov.ge/ka/document/view/{document_number}#article_{article_number}
```

---

## Georgian Text Processing

### Unicode Range
Georgian Mkhedruli script: U+10D0 to U+10FF (48 characters)

### Key Legal Terms

| Georgian | Transliteration | English |
|----------|---------------|---------|
| მუხლი | mukhli | Article |
| კოდექსი | kodeksi | Code |
| კანონი | kanoni | Law |
| სასჯელი | sasjeli | Punishment |
| ჯარიმა | jarima | Fine |
| თავისუფლების აღკვეთა | tavisuplebis aghkveta | Imprisonment |
| პირობითი სასჯელი | pirobiti sasjeli | Suspended sentence |
| შემამსუბუქებელი | shemamsubuqebeli | Mitigating (circumstances) |
| დამამძიმებელი | damamdzimebeli | Aggravating (circumstances) |
| ქურდობა | qurdoba | Theft |
| ყაჩაღობა | qachagoba | Robbery |
| თაღლითობა | taglitoba | Fraud |

### Always use UTF-8. Never ASCII operations on Georgian text.
