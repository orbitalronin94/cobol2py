#!/usr/bin/env python3
"""Validate the static inventory for the MIT-100 COBOL corpus."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "benchmarks" / "mit-100" / "manifest.json"

def main() -> int:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    entries = data.get("entries", [])
    ids = [entry.get("program_id") for entry in entries]
    errors = []
    if len(entries) != 100:
        errors.append(f"expected 100 entries, got {len(entries)}")
    if len(set(ids)) != 100:
        errors.append(f"expected 100 unique PROGRAM-ID values, got {len(set(ids))}")
    for entry in entries:
        if entry.get("license") != "MIT":
            errors.append(f"{entry.get('program_id')}: license is not MIT")
        path = ROOT / entry["path"]
        if not path.is_file():
            errors.append(f"{entry.get('program_id')}: missing source file {entry['path']}")
            continue
        content = path.read_text(encoding="utf-8", errors="replace")
        if entry["program_id"].upper() not in content.upper():
            errors.append(f"{entry.get('program_id')}: ID not found in {entry['path']}")
    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors), file=sys.stderr)
        return 1
    print(f"OK: {len(entries)} MIT-labelled entries, {len(set(ids))} unique IDs; source files present.")
    print("This validates inventory only; it does not compile or test COBOL behavior.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
