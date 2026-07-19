#!/usr/bin/env python3
"""Merge certification run batches into the final scorecard markdown."""
import json, sys

RUNS = [
    ('eval/results/golden/20260719_121825_certfinal', 'batch 1 (full 30)'),
    ('eval/results/golden/20260719_124206_certfix', 'batch 2 (9 re-runs)'),
    ('eval/results/golden/20260719_125017_certfix2', 'batch 3 (3 re-runs)'),
    ('eval/results/golden/20260719_125342_certfix3', 'batch 4 (2 re-runs)'),
]

merged = {}
for run, label in RUNS:
    try:
        d = json.load(open(f'{run}/report.json'))
    except FileNotFoundError:
        continue
    for r in d['results']:
        r['_batch'] = label
        r['_run'] = run
        merged[r['id']] = r

order = sorted(merged, key=lambda k: int(k[1:]))
passed = sum(1 for k in order if merged[k]['all_pass'])
lines = [
    f"Final result: **{passed}/{len(order)} golden questions pass all automated checks C1–C8**.",
    "Each row shows the question's final (post-fix) run; per-question responses and full",
    "traces are archived under the listed run directory.",
    "",
    "| id | domain | C1 | C2 | C3 | C4 | C5 | C6 | C7 | C8 | trace | batch |",
    "|----|--------|----|----|----|----|----|----|----|----|-------|-------|",
]
for k in order:
    r = merged[k]
    marks = " | ".join("✅" if r['checks'][f'C{i}']['pass'] else "❌" for i in range(1, 9))
    lines.append(
        f"| {k} | {r['domain']} | {marks} | `{r['trace_id'][:8]}…` | {r['_batch'].split()[1]} |"
    )
fails = [k for k in order if not merged[k]['all_pass']]
if fails:
    lines.append("")
    lines.append("Remaining failures: " + ", ".join(
        f"{k} ({', '.join(c for c in merged[k]['checks'] if not merged[k]['checks'][c]['pass'])})"
        for k in fails))
print("\n".join(lines))
json.dump({k: merged[k] for k in order},
          open('/private/tmp/claude-501/-Users-fuzzzybot-programming-fuzzzy-organisation-the-master-of-law/52770640-359e-4a33-b547-3976574c16e9/scratchpad/final_scorecard.json', 'w'),
          ensure_ascii=False, indent=1)
