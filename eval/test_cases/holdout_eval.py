#!/usr/bin/env python3
"""
Held-out evaluation for multi-source RAG.

Removes overlapping eval cases from ChromaDB court_practice collection,
runs the eval, then restores them — zero re-embedding.

Usage:
  # 1. Hold out cases (removes from ChromaDB, saves backup)
  python3 holdout_eval.py holdout

  # 2. Show what was held out
  python3 holdout_eval.py status

  # 3. Restore held-out cases back to ChromaDB
  python3 holdout_eval.py restore

  # Full cycle:
  python3 holdout_eval.py holdout
  python3 run_eval.py --limit 10   # run your eval
  python3 holdout_eval.py restore
"""

import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
PROJECT_ROOT = BASE_DIR.parent.parent
CHROMA_DIR = PROJECT_ROOT / "law_corpus" / "data" / "chroma"
CASES_FILE = BASE_DIR / "cases.json"
BACKUP_FILE = BASE_DIR / "holdout_backup.json"

# ── Case ID mapping ─────────────────────────────────────────
# Eval uses latin prefixes (as-, bs-), ChromaDB uses Georgian (ას-, ბს-)

LATIN_TO_GEORGIAN = {
    "as-": "ას-",
    "bs-": "ბს-",
}


def eval_source_to_chroma_id(source_file: str) -> str:
    """Convert eval source_file to ChromaDB case_id."""
    name = source_file.replace(".txt", "")
    # Convert Latin prefixes to Georgian
    for lat, geo in LATIN_TO_GEORGIAN.items():
        if name.startswith(lat):
            name = geo + name[len(lat):]
            break
    # Convert Latin 'ap' to Georgian 'აპ' (criminal case numbers)
    name = name.replace("ap", "აპ")
    return name


def find_overlapping_cases() -> list[dict]:
    """Find eval cases that exist in the court_practice collection."""
    with open(CASES_FILE, "r", encoding="utf-8") as f:
        eval_cases = json.load(f)["cases"]

    import chromadb
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    try:
        coll = client.get_collection("court_practice")
    except Exception:
        print("❌ court_practice collection not found")
        return []

    overlaps = []
    for case in eval_cases:
        chroma_id = eval_source_to_chroma_id(case.get("source_file", ""))
        # Check if this case_id exists in ChromaDB
        results = coll.get(where={"case_id": chroma_id}, limit=1)
        if results["ids"]:
            overlaps.append({
                "eval_case_id": case["case_id"],
                "chroma_case_id": chroma_id,
                "category": case["category"],
                "chunk_count": len(results["ids"]),
            })

    return overlaps


def holdout():
    """Remove overlapping cases from ChromaDB and save backup."""
    import chromadb

    print("=" * 60)
    print("🔬 Held-Out Evaluation — Remove Overlapping Cases")
    print("=" * 60)

    if BACKUP_FILE.exists():
        print("⚠️  Backup file already exists! Restore first or delete it.")
        print(f"   {BACKUP_FILE}")
        sys.exit(1)

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    coll = client.get_collection("court_practice")
    initial_count = coll.count()

    with open(CASES_FILE, "r", encoding="utf-8") as f:
        eval_cases = json.load(f)["cases"]

    backup_data = {
        "initial_collection_count": initial_count,
        "held_out_cases": [],
    }

    # Phase 1: COLLECT all data (no deletions yet)
    for case in eval_cases:
        chroma_id = eval_source_to_chroma_id(case.get("source_file", ""))

        # Get ALL chunks for this case (with embeddings for restore)
        results = coll.get(
            where={"case_id": chroma_id},
            include=["embeddings", "documents", "metadatas"],
        )

        if not results["ids"]:
            continue

        backup_data["held_out_cases"].append({
            "eval_case_id": case["case_id"],
            "chroma_case_id": chroma_id,
            "ids": results["ids"],
            "embeddings": results["embeddings"],
            "documents": results["documents"],
            "metadatas": results["metadatas"],
        })
        print(f"  📋 {case['case_id']:30s} → found {len(results['ids'])} chunks (case_id={chroma_id})")

    if not backup_data["held_out_cases"]:
        print("\n⚠️  No overlapping cases found. Nothing to hold out.")
        return

    # Phase 2: SAVE backup to disk BEFORE any deletion
    import numpy as np
    def _convert(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.generic):
            return obj.item()
        if isinstance(obj, list):
            return [_convert(x) for x in obj]
        if isinstance(obj, dict):
            return {k: _convert(v) for k, v in obj.items()}
        return obj

    backup_data = _convert(backup_data)

    with open(BACKUP_FILE, "w", encoding="utf-8") as f:
        json.dump(backup_data, f, ensure_ascii=False)
    print(f"\n  💾 Backup saved: {BACKUP_FILE}")

    # Phase 3: NOW delete from ChromaDB (backup is safely on disk)
    total_removed = 0
    for case_data in backup_data["held_out_cases"]:
        coll.delete(ids=case_data["ids"])
        total_removed += len(case_data["ids"])
        print(f"  🗑️  {case_data['eval_case_id']:30s} → removed {len(case_data['ids'])} chunks")

    final_count = coll.count()

    print(f"\n{'='*60}")
    print(f"✅ Held out {len(backup_data['held_out_cases'])} cases ({total_removed} chunks)")
    print(f"   Collection: {initial_count} → {final_count} chunks")
    print(f"   Backup: {BACKUP_FILE}")
    print(f"\n   Now run your eval, then restore with:")
    print(f"   python3 holdout_eval.py restore")


def restore():
    """Restore held-out cases back to ChromaDB from backup."""
    import chromadb

    print("=" * 60)
    print("🔄 Restoring Held-Out Cases")
    print("=" * 60)

    if not BACKUP_FILE.exists():
        print("❌ No backup file found. Nothing to restore.")
        sys.exit(1)

    with open(BACKUP_FILE, "r", encoding="utf-8") as f:
        backup_data = json.load(f)

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    coll = client.get_collection("court_practice")
    before_count = coll.count()

    total_restored = 0
    for case_data in backup_data["held_out_cases"]:
        coll.add(
            ids=case_data["ids"],
            embeddings=case_data["embeddings"],
            documents=case_data["documents"],
            metadatas=case_data["metadatas"],
        )
        total_restored += len(case_data["ids"])
        print(f"  ✅ {case_data['eval_case_id']:30s} → restored {len(case_data['ids'])} chunks")

    after_count = coll.count()

    # Remove backup file
    BACKUP_FILE.unlink()

    print(f"\n{'='*60}")
    print(f"✅ Restored {len(backup_data['held_out_cases'])} cases ({total_restored} chunks)")
    print(f"   Collection: {before_count} → {after_count} chunks")
    print(f"   Expected: {backup_data['initial_collection_count']}")


def status():
    """Show current held-out status."""
    import chromadb

    print("=" * 60)
    print("📊 Held-Out Status")
    print("=" * 60)

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    for name in ["georgian_laws", "court_practice", "grand_chamber"]:
        try:
            coll = client.get_collection(name)
            print(f"  {name}: {coll.count()} chunks")
        except Exception:
            print(f"  {name}: not found")

    if BACKUP_FILE.exists():
        try:
            with open(BACKUP_FILE, "r", encoding="utf-8") as f:
                backup = json.load(f)
            cases = backup["held_out_cases"]
            total_chunks = sum(len(c["ids"]) for c in cases)
            print(f"\n  ⚠️  {len(cases)} cases held out ({total_chunks} chunks)")
            print(f"     Original collection size: {backup['initial_collection_count']}")
            for c in cases[:5]:
                print(f"     - {c['eval_case_id']}: {len(c['ids'])} chunks")
            if len(cases) > 5:
                print(f"     ... +{len(cases)-5} more")
        except (json.JSONDecodeError, KeyError) as e:
            print(f"\n  ❌ Backup file exists but is corrupt: {e}")
            print(f"     Delete it and rebuild: rm {BACKUP_FILE}")
    else:
        print(f"\n  ✅ No cases held out — all data in collections")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 holdout_eval.py [holdout|restore|status]")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "holdout":
        holdout()
    elif cmd == "restore":
        restore()
    elif cmd == "status":
        status()
    else:
        print(f"Unknown command: {cmd}")
        print("Usage: python3 holdout_eval.py [holdout|restore|status]")
        sys.exit(1)
