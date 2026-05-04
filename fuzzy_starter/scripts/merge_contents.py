"""
Merge the contents of every file with a chosen extension inside a directory
(recursively) into one big text file.

Examples
--------

# merge every .py file under src/ → outputs/src.txt
python scripts/merge_contents.py src --ext .py

# merge .txt files under conversations/ → outputs/conversations.txt
python scripts/merge_contents.py conversations --ext .txt
"""

from __future__ import annotations

import argparse
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Concatenate many files into one readable text blob."
    )
    parser.add_argument(
        "directory",
        help="Root directory to walk (processed recursively).",
    )
    parser.add_argument(
        "--ext",
        default=".dart",
        help="File extension to include (default: .txt). "
        "Add the dot or not, both work.",
    )
    parser.add_argument(
        "--out-dir",
        default=str(Path(__file__).parent / "outputs"),
        help="Destination directory for the merged file "
        "(default: ../outputs/merged/ relative to project root).",
    )
    return parser.parse_args()


def merge(directory: str | Path, ext: str, out_dir: str | Path) -> None:
    root = Path(directory).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"{root} does not exist")

    ext = ext if ext.startswith(".") else f".{ext}"
    out_dir = Path(out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    top_name = root.name
    if top_name.endswith(ext):
        top_name = top_name[: -len(ext)]
    out_file = out_dir / f"{top_name}.txt"

    count = 0
    with out_file.open("w", encoding="utf-8") as merged:
        for path in sorted(root.rglob(f"*{ext}")):
            if path.name.endswith(".g.py"):
                continue
            count += 1
            merged.write(
                f"-----Content from: {root.name}/{path.relative_to(root)}-----\n\n"
            )
            merged.write(path.read_text(encoding="utf-8"))
            merged.write("\n\n")

    print(f"✓ merged {count} file(s) → {out_file}")


if __name__ == "__main__":
    args = parse_args()
    merge(args.directory, args.ext, args.out_dir)
